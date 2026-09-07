import os
import csv
import gzip
import yaml
import sys
try:
    import pysam
    HAS_PYSAM = True
except ImportError:
    HAS_PYSAM = False
import time
import requests
import hashlib
import xml.etree.ElementTree as ET
import concurrent.futures
from yaspin import yaspin

from submg.modules import loggingC
from submg.modules.statConf import staticConfig


# Global variable for timestamping data that is pulled from the config
timestamp = None
keys_to_stamp = []

# Credentials
USE_GUI = False
gui_credentials = {"username": None, "password": None}

def set_gui_credentials(username, password):
    """
    Set the credentials when using the GUI.

    Args:
        username (str): ENA username.
        password (str): ENA password.
    """
    global USE_GUI
    USE_GUI = True
    gui_credentials["username"] = username
    gui_credentials["password"] = password


def full_timestamp():
    """
    Creates and returns a full timestamp (year, month, day, hour, minute, second).
    """
    timestamp = time.strftime("%Y_%m_%d_%H%M%S")
    return timestamp


def set_up_timestamps(arguments: dict):
    """
    Set up the timestamp for the submission. Data is only timestamped with
    the hour, minute and second. Because of daily resets, this is sufficient to
    prevent name clashes on the development server.
    """
    global timestamp
    global keys_to_stamp
    keys_to_stamp = [
        "PROJECT_NAME",
        "NAME",
        "TITLE",
        "RELATED_SAMPLE_TITLE"
    ]
    if arguments['submit_assembly']:
        keys_to_stamp.append("ASSEMBLY_NAME")
    timestamp = time.strftime("%H%M%S")


def set_up_staging(staging_dir: str,
                   timestamp: str):
    """
    Set up the staging subdirectory for the submission. Make sure it is empty.

    Args:
        staging_dir: The path to the parent staging directory.
        timestamp: The timestamp for the submission.
    """
    if not os.path.exists(staging_dir):
        os.makedirs(staging_dir)

    stamped_staging_dir = os.path.join(staging_dir, timestamp)

    if os.path.exists(stamped_staging_dir):
        err = f"\nERROR: Staging directory already exists: {stamped_staging_dir}"
        loggingC.message(err, threshold=-1)
        sys.exit(1)

    os.makedirs(stamped_staging_dir)

    if not os.path.exists(stamped_staging_dir):
        err = f"\nERROR: Could not create staging directory at {stamped_staging_dir}"
        loggingC.message(err, threshold=-1)
        sys.exit(1)

    return stamped_staging_dir


def check_bam_basenames(bam_files):
    """
    Stop if multiple BAM files would produce the same depth-file basename.

    Args:
        bam_files: A BAM file path or a list of BAM file paths.
    """
    if not isinstance(bam_files, list):
        bam_files = [bam_files]

    basenames = {}
    for bam_file in bam_files:
        basename = os.path.basename(bam_file)
        basenames.setdefault(basename, []).append(bam_file)

    duplicate_basenames = {
        basename: paths
        for basename, paths in basenames.items()
        if len(paths) > 1
    }
    if not duplicate_basenames:
        return

    collisions = "\n".join(
        f"\t{basename}: {', '.join(paths)}"
        for basename, paths in sorted(duplicate_basenames.items())
    )
    err = (
        "\nERROR: BAM files must have unique basenames because. "
        "The following basenames are used "
        f"by multiple files:\n{collisions}"
    )
    loggingC.message(err, threshold=-1)
    sys.exit(1)


def construct_depth_files(staging_dir: str,
                          threads: int,
                          bam_files: list) -> list:
    """
    Construct depth files from bam files.

    Args:
        staging_dir: The staging directory.
        threads: The total number of threads to use.
        bam_files: The list of bam files.
    """
    if not isinstance(bam_files, list):
        bam_files = [bam_files]
    check_bam_basenames(bam_files)

    loggingC.message(">Constructing depth files from bam files. This might take a while.", threshold=0)
    
    depth_directory = os.path.join(staging_dir, 'depth')
    os.makedirs(depth_directory, exist_ok=True)
    
    threads_per_file = max(1, threads // len(bam_files))
    max_workers = min(threads, len(bam_files))

    with yaspin(text=f"Processing {len(bam_files)} bam files with {threads_per_file} threads each...\t", color="yellow") as spinner:

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_depth_file = {
                    executor.submit(make_depth_file, bam_file, depth_directory, num_threads=threads_per_file): bam_file
                    for bam_file in bam_files
                }
                depth_files = []

                for future in concurrent.futures.as_completed(future_to_depth_file):
                    bam_file = future_to_depth_file[future]
                    try:
                        depth_file = future.result()
                        depth_files.append(depth_file)
                    except Exception as exc:
                        loggingC.message(f"{bam_file} generated an exception: {exc}", threshold=-1)
                        raise

    return depth_files


def build_sample_submission_xml(outpath: str,
                                  hold_until_date: str = None):
    """
    Build an ENA submission XML file for uploading sample data.

    Args:
        outpath (str): The output path for the submission.xml file.
    """
    loggingC.message(f">Building sample submission.xml file...", threshold=0)

    root = ET.Element("SUBMISSION")
    actions = ET.SubElement(root, "ACTIONS")
    action = ET.SubElement(actions, "ACTION")
    add = ET.SubElement(action, "ADD")
    action2 = ET.SubElement(actions, "ACTION")
    if hold_until_date is None:
        add = ET.SubElement(action2, "RELEASE")
    else:
        add = ET.SubElement(action2, "HOLD", HoldUntilDate=hold_until_date)

    tree = ET.ElementTree(root)
    #Skipping indentation for python3.8 compatibility
    #ET.indent(tree, space="\t", level=0)

    with open(outpath, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True)
    
    loggingC.message(f"\t...written to {os.path.abspath(outpath)}", threshold=0)


def format_receipt_failure(root, receipt_path, submission_name):
    """Format an ENA rejection and include errors recorded in its receipt."""
    receipt_path = os.path.abspath(receipt_path)
    ena_errors = [
        ''.join(error.itertext()).strip()
        for error in root.iter('ERROR')
        if ''.join(error.itertext()).strip()
    ]
    ena_report = '\n'.join(f"  - {error}" for error in ena_errors)
    if not ena_report:
        ena_report = "  <no detailed error message in receipt>"

    return (
        f"ERROR: ENA rejected the {submission_name} submission.\n\n"
        f"Receipt:\n  {receipt_path}\n\n"
        f"ENA reported:\n{ena_report}\n\n"
        "Likely cause:\n"
        "  The submitted metadata did not satisfy ENA requirements\n\n"
        "How to proceed:\n"
        "  - Review the ENA messages above\n"
        f"  - Check the complete receipt at {receipt_path}\n"
        "  - Correct the metadata and retry"
    )


def api_response_check(response: requests.Response, submission_xml=None):
    if response.status_code == 403:
        err = (
            "ERROR: ENA authentication failed.\n\n"
            f"Endpoint:\n  {response.url}\n\n"
            f"HTTP status:\n  {response.status_code} {response.reason}\n\n"
            "Likely cause:\n"
            "  ENA rejected the supplied Webin credentials\n\n"
            "Recommended actions:\n"
            "  - Verify that ENA_USER contains your Webin account name\n"
            "  - Verify that ENA_PASSWORD contains the corresponding password\n"
            "  - Confirm the credentials by signing in to the ENA Webin portal\n"
            "  - Check whether you are using the intended development or production service"
        )
        loggingC.message(err, threshold=-1)
        sys.exit(1)

    if response.status_code != 200 or not response.text:
        response_text = response.text.strip() or '<empty>'
        response_text = response_text.replace('\n', '\n  ')
        if response.status_code == 400:
            likely_cause = "ENA rejected the submitted metadata or XML"
        elif response.status_code == 408:
            likely_cause = "The request to ENA timed out"
        elif response.status_code >= 500:
            likely_cause = "The ENA service encountered a temporary server error"
        elif not response.text:
            likely_cause = "ENA returned an empty response"
        else:
            likely_cause = "unknown"

        err = (
            "ERROR: ENA API request failed.\n\n"
            f"Endpoint:\n  {response.url}\n\n"
            f"HTTP status:\n  {response.status_code} {response.reason}\n\n"
            f"ENA response:\n  {response_text}\n\n"
            f"Likely cause:\n  {likely_cause}\n\n"
            "How to proceed:\n"
            "  - Review the ENA response above"
        )
        if submission_xml is not None:
            err += (
                "\n  - Check the generated submission XML at "
                f"{os.path.abspath(submission_xml)}"
            )
        loggingC.message(err, threshold=-1)
        sys.exit(1)


def calculate_md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_login():
    """
    Reads ENA login credentials and returns them.
    Uses environment variables or GUI inputs based on the context.

    Returns:
        (str, str): Username and Password.
    """
    if USE_GUI:
        if gui_credentials["username"] is None or gui_credentials["password"] is None:
            err = "\nERROR: GUI credentials not set."
            loggingC.message(err, threshold=-1)
            sys.exit(1)
        return gui_credentials["username"], gui_credentials["password"]
    
    # Fallback to environment variables for CLI usage
    if 'ENA_USER' not in os.environ:
        err = "\nERROR: ENA_USER environmental variable not set. Please export your ENA username as ENA_USER."
        loggingC.message(err, threshold=-1)
        sys.exit(1)
    if 'ENA_PASSWORD' not in os.environ:
        err = "\nERROR: ENA_PASSWORD environmental variable not set. Please export your ENA password as ENA_PASSWORD."
        loggingC.message(err, threshold=-1)
        sys.exit(1)

    return os.environ['ENA_USER'], os.environ['ENA_PASSWORD']



def read_yaml(file_path, convert_file_paths=True):
    """ 
    Reads a YAML file and returns the data as a dictionary.

    Args:
        file_path (str): The path to the YAML file.
        convert_file_paths (bool): If True, file paths will be converted to
                                   absolute paths.
    """
    def convert_paths(data, base_path):
        """
        Recursively converts relative file paths in the dictionary to absolute paths.
        
        Args:
            data: The dictionary or list to process.
            base_path: The base directory to resolve relative paths.

        Returns:
            The dictionary or list with converted file paths.
        """
        if isinstance(data, dict):
            return {
                key: convert_paths(value, base_path) 
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [convert_paths(item, base_path) for item in data]
        elif isinstance(data, str):
            # Check if the string is a relative path
            if not os.path.isabs(data) and os.path.exists(os.path.join(base_path, data)):
                return os.path.abspath(os.path.join(base_path, data))
        return data

    config_path = os.path.abspath(file_path)
    try:
        with open(config_path, 'r') as yaml_file:
            data = yaml.safe_load(yaml_file)
            if convert_file_paths:
                base_path = os.path.dirname(config_path)
                data = convert_paths(data, base_path)
            return data
    except FileNotFoundError:
        err = (
            "ERROR: Configuration file not found.\n\n"
            f"Configuration file:\n  {config_path}\n\n"
            "Likely cause:\n"
            "  The configured path does not point to an existing file\n\n"
            "How to proceed:\n"
            "  - Check the configuration-file path and try again"
        )
        loggingC.message(err, threshold=-1)
        sys.exit(1)
    except PermissionError as e:
        err = (
            "ERROR: Cannot read the configuration file.\n\n"
            f"Configuration file:\n  {config_path}\n\n"
            f"System error:\n  {e}\n\n"
            "Likely cause:\n"
            "  Permission to read the configuration file was denied\n\n"
            "How to proceed:\n"
            "  - Check the file permissions and try again"
        )
        loggingC.message(err, threshold=-1)
        sys.exit(1)
    except yaml.YAMLError as e:
        parser_message = getattr(e, 'problem', None) or str(e)
        parser_message = parser_message.replace('\n', '\n  ')
        mark = getattr(e, 'problem_mark', None)
        location = ''
        location_hint = ''
        if mark is not None:
            line = mark.line + 1
            column = mark.column + 1
            location = f"\nLocation:\n  line {line}, column {column}\n"
            location_hint = f" near line {line}"
        err = (
            "ERROR: Could not parse the configuration file.\n\n"
            f"Configuration file:\n  {config_path}\n\n"
            f"Parser message:\n  {parser_message}\n"
            f"{location}\n"
            "Likely cause:\n"
            "  The YAML structure or indentation is invalid\n\n"
            "How to proceed:\n"
            f"  - Inspect the configuration{location_hint}\n"
            "  - Check indentation, colons, quotes, and list markers\n"
            "  - Correct the YAML and try again"
        )
        loggingC.message(err, threshold=-1)
        sys.exit(1)
    except OSError as e:
        err = (
            "ERROR: Could not read the configuration file.\n\n"
            f"Configuration file:\n  {config_path}\n\n"
            f"System error:\n  {e}\n\n"
            "Likely cause:\n"
            "  The operating system could not read the file\n\n"
            "How to proceed:\n"
            "  - Check that the path is a readable regular file and try again"
        )
        loggingC.message(err, threshold=-1)
        sys.exit(1)
    except Exception as e:
        err = (
            "ERROR: Unexpected error while processing the configuration file.\n\n"
            f"Configuration file:\n  {config_path}\n\n"
            f"Error:\n  {type(e).__name__}: {e}"
        )
        loggingC.message(err, threshold=-1)
        sys.exit(1)



def __strcast(value):
    """
    Cast integers and floats to string. If the input is a list, set or dict,
    call this function on each value.
    
    Args:
        value: The value to cast to string.
    """
    if type(value) == int or type(value) == float:
        return str(value)
    if type(value) == list:
        return [__strcast(v) for v in value]
    if type(value) == set:
        return {__strcast(v) for v in value}
    if type(value) == dict:
        return {k: __strcast(v) for k, v in value.items()}
    return value


def prepdir(parent_path, name):
    parent_path = os.path.abspath(parent_path)
    if not os.path.isdir(parent_path):
        err = f"\nERROR: The path {parent_path} is not a directory."
        loggingC.message(err, threshold=-1)
        sys.exit(1)
    newdir = os.path.join(parent_path, name)
    os.makedirs(newdir, exist_ok=False)
    return newdir


def from_config(config, key, subkey=None, subsubkey=None, supress_errors=False):
    """
    Extracts a value from the dict that was created based on the
    config YAML file.

    Args:
        config (dict): The dict created from the config YAML file.
        key (str): The key to extract from the dict.
        subkey (str): The nested key to extract from the key.
        subsubkey (str): The nested key to extract from the subkey.
        supress_errors (bool): If True, missing keys will not cause an exit
            but will instead return None.
    """
    if not key in config:
        if not supress_errors:
            err = f"\nERROR: The field '{key}' is missing from the config YAML file."
            loggingC.message(err, threshold=-1)
            sys.exit(1)
        else:
            return None
    if not config[key]:
        if not supress_errors:
            err = f"\nERROR: The field '{key}' is empty in the config YAML file."
            loggingC.message(err, threshold=-1)
            sys.exit(1)
        else:
            return None
    if subkey:
        if not subkey in config[key]:
            if not supress_errors:
                err = f"\nERROR: The field '{key}|{subkey}' is missing from the config YAML file."
                loggingC.message(err, threshold=-1)
                sys.exit(1)
            else:
                return None
        if not config[key][subkey]:
            if not supress_errors:
                err = f"\nERROR: The field '{key}|{subkey}' is empty in the config YAML file."
                loggingC.message(err, threshold=-1)
                sys.exit(1)
        if subsubkey:
            if not subsubkey in config[key][subkey]:
                if not supress_errors:
                    err = f"\nERROR: The field '{key}|{subkey}|{subsubkey}' is missing from the config YAML file."
                    loggingC.message(err, threshold=-1)
                    sys.exit(1)
                else:
                    return None
            if not config[key][subkey][subsubkey]:
                if not supress_errors:
                    err = f"\nERROR: The field '{key}|{subkey}|{subsubkey}' is empty in the config YAML file."
                    loggingC.message(err, threshold=-1)
                    sys.exit(1)
                else:
                    return None
            return __strcast(config[key][subkey][subsubkey])
        return __strcast(config[key][subkey])
    return __strcast(config[key])


def samples_from_reads(config):
    """
    Extracts the a list of sample accessions from the SINGLE_READS and
    PAIRED_END_READS fields in the config.
    
    Args:
        config (dict): The dict created from the config YAML file.

    Returns:
        list: List of sample accessions.
    """
    samples = set()
    if 'SINGLE_READS' in config:
        for read in config['SINGLE_READS']:
            if not 'RELATED_SAMPLE_ACCESSION' in read:
                err = "\nERROR: Trying to read the RELATED_SAMPLE_ACCESION "
                err += "field from an entry in the SINGLE_READS section of "
                err += "the config, but the field is missing.\n"
                err += "When submitting reads but not submitting samples, "
                err += "the RELATED_SAMPLE_ACCESSION field must be present for "
                err += "each read entry."
                loggingC.message(err, threshold=-1)
                sys.exit(1)
            samples.add(read['RELATED_SAMPLE_ACCESSION'])
    if 'PAIRED_END_READS' in config:
        for read in config['PAIRED_END_READS']:
            if not 'RELATED_SAMPLE_ACCESSION' in read:
                err = "\nERROR: Trying to read the RELATED_SAMPLE_ACCESION "
                err += "field from an entry in the PAIRED_END_READS section of "
                err += "the config, but the field is missing.\n"
                err += "When submitting reads but not submitting samples, "
                err += "the RELATED_SAMPLE_ACCESSION field must be present for "
                err += "each read entry."
                loggingC.message(err, threshold=-1)
                sys.exit(1)
            samples.add(read['RELATED_SAMPLE_ACCESSION'])
    return list(samples)


def optional_from_config(config, key, subkey=None, subsubkey=None):
    """
    Calls from config but returns None if the key is missing.

    Args:
        config (dict): The dict created from the config YAML file.
        key (str): The key to extract from the dict.
        subkey (str): The nested key to extract from the key.
        subsubkey (str): The nested key to extract from the subkey.
    """
    try:
        return from_config(config, key, subkey, subsubkey, supress_errors=True)
    except:
        return None
    

def stamped_from_config(config, key, subkey=None, subsubkey=None):
    """
    Calls from config but adds a timestamp to relevant fields if timestamping
    is activated.

    Args:
        config (dict): The dict created from the config YAML file.
        key (str): The key to extract from the dict.
        subkey (str): The nested key to extract from the key.
        subsubkey (str): The nested key to extract from the subkey.
    """
    lowest_key = subsubkey or subkey or key

    value = from_config(config, key, subkey, subsubkey)
    if timestamp and (lowest_key in keys_to_stamp):
        value = f"{timestamp}{value}"
    return value


def check_fastq(fastq_filepath: str):
    """
    Checks if the FASTQ file exists and has a valid extension.

    Args:
        fastq_filepath (str): The path to the FASTQ file.
    """
    if fastq_filepath.lower().endswith('.gz'):
        extension_path = fastq_filepath[:-3]
    else:
        extension_path = fastq_filepath

    if not os.path.isfile(fastq_filepath):
        err = f"\nERROR: The FASTQ file '{fastq_filepath}' does not exist."
        loggingC.message(err, threshold=-1)
        sys.exit(1)

    extensions = staticConfig.fastq_extensions.split(';')
    if not extension_path.endswith(tuple(extensions)):
        err = f"\nERROR: The FASTQ file '{fastq_filepath}' has an invalid extension. Valid extensions are {'|'.join(extensions)}."
        loggingC.message(err, threshold=-1)
        sys.exit(1)


def open_fastq(fastq_filepath: str, mode: str = 'rb'):
    """
    Open a plain or gzip-compressed FASTQ file.

    Args:
        fastq_filepath (str): The path to the FASTQ file.
        mode (str): The file-open mode.

    Returns:
        A file object for the FASTQ file.
    """
    if fastq_filepath.lower().endswith('.gz'):
        return gzip.open(fastq_filepath, mode)
    return open(fastq_filepath, mode)


def fastq_header_content(header_line: bytes) -> bytes:
    """
    Return a FASTQ header without its line ending.

    Args:
        header_line (bytes): The first line of a FASTQ record.

    Returns:
        The header content without trailing carriage-return or newline bytes.
    """
    return header_line.rstrip(b'\r\n')


def check_fastq_read_names(fastq_filepath: str,
                           read_count: int = staticConfig.fastq_preflight_read_count):
    """
    Check the first ``read_count`` FASTQ records for long read names.

    Args:
        fastq_filepath (str): The path to the FASTQ file.
        read_count (int): The maximum number of records to inspect.

    Returns:
        A tuple containing the 1-based read number and header length for the
        first violation, or None if no violation is found.
    """
    lines_to_check = read_count * 4
    with open_fastq(fastq_filepath, 'rb') as fastq_file:
        for line_number in range(lines_to_check):
            line = fastq_file.readline()
            if not line:
                break
            if line_number % 4 == 0:
                header_length = len(fastq_header_content(line))
                if header_length > staticConfig.max_fastq_read_name_length:
                    read_number = (line_number // 4) + 1
                    return read_number, header_length
    return None


def is_fasta(filepath, extensions=staticConfig.fasta_extensions.split(';')) -> str:
    """
    Checks if the file at filepath is a FASTA file. Return the basename if it is.
    Return None otherwise.

    Args:
        filepath (str): The path to the file.
        extensions (list): List of allowed extensions.

    Returns:
        str: The basename of the file if it is a FASTA file, None otherwise.
    """
    if not os.path.isfile(filepath):
        return None
    if filepath.lower().endswith('.gz'):
        filepath = filepath[:-3]
    if not filepath.lower().endswith(tuple(extensions)):
        return None
    filename = os.path.basename(filepath)
    basename = filename.rsplit('.', 1)[0]
    return basename


def check_fasta(fasta_path) -> tuple:
    """
    Checks if the fasta file exists, has a valid extension and whether it is
    gzipped or not.

    Args:
        fasta_path (str): The path to the fasta file.

    Returns:
        Tuple[str, bool]: The path to the fasta file and whether it is gzipped.
    """
    if fasta_path is None or fasta_path is False or fasta_path == "":
        err = "\nERROR: Trying to submit assembly, but no FASTA file is provided in the description."
        loggingC.message(err, threshold=-1)
        sys.exit(1)
    elif not os.path.isfile(fasta_path):
        err = f"\nERROR: Trying to submit assembly, but the FASTA file {fasta_path} does not exist."
        loggingC.message(err, threshold=-1)
        sys.exit(1)
    extension = fasta_path.split('.')[-1].lower()
    gzipped = False
    if extension == 'gz':
        gzipped = True
        extension = fasta_path.split('.')[-2].lower()
    if not extension in staticConfig.fasta_extensions:
        err = f"\nERROR: fasta file at {fasta_path} has an unknown file extension ({extension}). Allowed extensions are {staticConfig.fasta_extensions} (+.gz)."
        loggingC.message(err, threshold=-1)
        sys.exit(1)
    return fasta_path, gzipped


def quality_filter_bins(quality_data, config):
    """
    Filter bins based on the quality data.

    Args:
        quality_data (dict): The quality data for the bins.
    """
    filtered_bins = []

    # Check arguments in config
    if 'MIN_COMPLETENESS' in config['BINS']:
        min_completeness = float(config['BINS']['MIN_COMPLETENESS'])
        msg = f">Filtering bins based on minimum completeness of {min_completeness}."
    else:
        min_completeness = 0
        msg = ">No MIN_COMPLETENESS specified, bins will not be filtered for completeness."
    loggingC.message(msg, threshold=0)
    if 'MAX_CONTAMINATION' in config['BINS']:
        max_contamination = float(config['BINS']['MAX_CONTAMINATION'])
        msg = f">Filtering bins based on maximum contamination of {max_contamination}."
    else:
        max_contamination = 100
        msg = ">No MAX_CONTAMINATION specified, maximum contamination is set to 100."
    loggingC.message(msg, threshold=0)

    # Filtering
    filtered_out = []
    for bin in quality_data:
        if quality_data[bin]['completeness'] >= min_completeness and quality_data[bin]['contamination'] <= max_contamination:
            filtered_bins.append(bin)
        else:
            filtered_out.append(bin)
    if len(filtered_out) > 0:
        msg = f">WARNING: {len(filtered_out)} bins have been excluded from submission due to quality thresholds:"
        loggingC.message(msg, threshold=0)
    for bin in filtered_out:
        msg = f"\t{bin} (completeness {quality_data[bin]['completeness']}, contamination {quality_data[bin]['contamination']})"
        loggingC.message(msg, threshold=0)
    if len(filtered_out) > 0:
        time.sleep(5) # Give user some extra time to notice message
    if len(filtered_bins) == 0:
        err = "\nERROR: No bins left after filtering. Please adjust the quality thresholds."
        loggingC.message(err, threshold=-1)
        sys.exit(1)
    return filtered_bins


def check_bam(bam_file,
              num_threads=4) -> str:
    """
    Checks if the BAM file exists, has a valid extension and whether it is
    sorted or not. If not, it will be sorted and indexed.

    Args:
        bam_file (str): The path to the BAM file.
        num_threads (int): The number of threads to use for sorting and indexing. 

    Returns:
        str: The path to the sorted and indexed BAM file.
    """
    if not HAS_PYSAM:
        err = "\nERROR: pysam is not installed, but needed for coverage calculations. You CANNOT use pysam on a windows system."
        loggingC.message(err, threshold=-1)
        sys.exit(1)

    # Check if the ending of the file is .bam or .BAM
    if bam_file.endswith('.BAM'):
        file_ending = '.BAM'
    elif bam_file.endswith('.bam'):
        file_ending = '.bam'
    else:
        ext = bam_file.split('.')[-1]
        err = f"\nERROR: The file {bam_file} has the unexpected extension {ext} (expected .bam or .BAM)."
        loggingC.message(err, threshold=-1)
        sys.exit(1)

    # Check if BAM file is sorted, sort it if not. This will also index the file.
    sorted_bam_file = bam_file
    try:
        pysam.index(sorted_bam_file)
    except:  # This might mean the bam file is not sorted, so we try that
        time.sleep(1)
        warn = f"WARNING: Cannot read {bam_file}. The file might be unsorted, trying to sort..."
        loggingC.message(warn, threshold=0)
        sorted_bam_file = bam_file[:len(bam_file) - len(file_ending)] + '.tmp.sorted' + file_ending
        pysam.sort("-o", sorted_bam_file, bam_file, "-@", str(num_threads))      
        time.sleep(1)
        pysam.index(sorted_bam_file)
        time.sleep(1)

    return sorted_bam_file  


def make_depth_file(bam_file, outdir, num_threads=4):
    """
    Uses pysam.depth to call samtools depth and create a depth file with
    the coverage per base per contig.

    Args:
        outdir (str): Path to the output directory.
        bam_file (str): Path to the BAM file.

    Returns:
        str: Path to the depth file.
    """
    if not HAS_PYSAM:
        err = "\nERROR: pysam is not installed, but needed for coverage calculations. You CANNOT use pysam on a windows system."
        loggingC.message(err, threshold=-1)
        sys.exit(1)
    sorted_bam_file = check_bam(bam_file, num_threads=num_threads)
    filename = os.path.basename(sorted_bam_file) + '.depth'
    outfile = os.path.join(outdir, filename)
    pysam.depth("-@", str(num_threads), "-aa", sorted_bam_file, "-o", outfile)
    return outfile


def contigs_coverage(depth_file):
    """
    Calculates the coverage per contig from a depth file.

    Args:
    depth_file (str): File path to the depth file.

    Returns:
    dict: Contig name as key, coverage as value.
    dict: Contig name as key, length as value.
    """
    contig_coverage = {}
    contig_length = {}
    reader = csv.reader(depth_file, delimiter='\t')
    for row in reader:
        contig = row[0].strip().split(' ')[0]
        position = int(row[1].strip())
        coverage = int(row[2].strip())
        if not contig in contig_coverage:
            contig_coverage[contig] = 0
            contig_length[contig] = 0
        contig_coverage[contig] += coverage
        if position > contig_length[contig]: # Contig positions should be ordered, so we just need the last one. But we do this just to be safe
            contig_length[contig] = position
    return contig_coverage, contig_length


def _read_depth_files(depth_files: list,
                      threads: int) -> tuple:
    """
    Read depth files once and sum depth per contig across all files.

    Args:
        depth_files: Paths to depth files.
        threads: Maximum number of concurrent workers.

    Returns:
        Tuple containing summed contig depths and one length per contig.
    """
    def process_file(depth_file):
        with open(depth_file, 'r') as depth:
            return contigs_coverage(depth)

    loggingC.message(">Calculating coverage from depth files. This might take a while.", threshold=0)
    inuse = min(max(1, threads), len(depth_files))
    with yaspin(text=f"Processing with {inuse} threads...\t", color="yellow") as spinner:
        with concurrent.futures.ThreadPoolExecutor(max_workers=inuse) as executor:
            results = executor.map(process_file, depth_files)

        total_depth = {}
        contig_lengths = {}
        for contig_depth, contig_length in results:
            for contig, depth in contig_depth.items():
                total_depth[contig] = total_depth.get(contig, 0) + depth
            for contig, length in contig_length.items():
                if contig not in contig_lengths:
                    contig_lengths[contig] = length

    return total_depth, contig_lengths


def _coverage_from_contigs(total_depth: dict,
                           contig_lengths: dict,
                           target_contigs=None) -> float:
    """Calculate coverage from already-summed per-contig depths."""
    if target_contigs is None:
        target_contigs = contig_lengths.keys()
    depth = sum(total_depth.get(contig, 0) for contig in target_contigs)
    length = sum(contig_lengths.get(contig, 0) for contig in target_contigs)
    coverage = depth / length if length > 0 else 0.0
    return round(coverage, 1)


def _bin_contigs(config: dict,
                 filtered_bins: list) -> dict:
    """Read the contig names for each filtered bin."""
    bins_directory = from_config(config, 'BINS', 'BINS_DIRECTORY')
    filtered_bins = set(filtered_bins)
    bin_contigs = {}

    for filename in os.listdir(bins_directory):
        fasta = os.path.join(bins_directory, filename)
        bin_name = is_fasta(fasta)
        if bin_name not in filtered_bins:
            continue

        fasta_handle = gzip.open(fasta, 'rt') if fasta.lower().endswith('.gz') else open(fasta, 'r')
        with fasta_handle as handle:
            bin_contigs[bin_name] = {
                line.strip().split(' ')[0][1:]
                for line in handle
                if line.startswith('>')
            }

    return bin_contigs


def _write_bin_coverage(outfile: str,
                        filtered_bins: list,
                        bin_coverages: dict) -> None:
    """Write bin coverage values in the configured TSV format."""
    with open(outfile, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['Bin_id', 'Coverage'])
        for bin_name in filtered_bins:
            writer.writerow([bin_name, bin_coverages[bin_name]])


def resolve_coverage(config: dict,
                     submit_assembly: bool,
                     submit_bins: bool,
                     submit_mags: bool,
                     filtered_bins: list,
                     staging_dir: str,
                     logging_dir: str,
                     threads: int,
                     minitest: bool,
                     keep_depth_files: bool) -> tuple:
    """Resolve all coverage needed by the requested submissions once."""
    assembly_required = submit_assembly
    bins_required = submit_bins or submit_mags

    assembly_coverage = None
    if assembly_required and 'COVERAGE_VALUE' in config.get('ASSEMBLY', {}):
        assembly_coverage = float(config['ASSEMBLY']['COVERAGE_VALUE'])

    bin_coverage_file = None
    if bins_required and 'COVERAGE_FILE' in config.get('BINS', {}):
        bin_coverage_file = config['BINS']['COVERAGE_FILE']

    assembly_missing = assembly_required and assembly_coverage is None
    bins_missing = bins_required and bin_coverage_file is None
    assembly_outfile = os.path.join(logging_dir, 'assembly_coverage.txt')
    bin_outfile = os.path.join(logging_dir, 'bin_coverages.tsv')

    if minitest:
        if assembly_missing:
            assembly_coverage = 1.0
        if bins_missing:
            mock_coverages = {bin_name: 1.0 for bin_name in filtered_bins}
            _write_bin_coverage(bin_outfile, filtered_bins, mock_coverages)
            bin_coverage_file = bin_outfile
        return assembly_coverage, bin_coverage_file

    depth_files = []
    try:
        if assembly_missing or bins_missing:
            bam_files = from_config(config, 'BAM_FILES')
            if not isinstance(bam_files, list):
                bam_files = [bam_files]
            depth_files = construct_depth_files(staging_dir, threads, bam_files)
            total_depth, contig_lengths = _read_depth_files(depth_files, threads)

            if assembly_missing:
                assembly_coverage = _coverage_from_contigs(total_depth,
                                                           contig_lengths)

            if bins_missing:
                contigs_by_bin = _bin_contigs(config, filtered_bins)
                bin_coverages = {
                    bin_name: _coverage_from_contigs(total_depth,
                                                     contig_lengths,
                                                     contigs_by_bin[bin_name])
                    for bin_name in filtered_bins
                }
                _write_bin_coverage(bin_outfile, filtered_bins, bin_coverages)
                bin_coverage_file = bin_outfile
    finally:
        if depth_files and not keep_depth_files:
            loggingC.message(">Deleting depth files to free up disk space. "
                             "To keep them in a future run use the "
                             "--keep-depth-files option.", threshold=0)
            for depth_file in depth_files:
                os.remove(depth_file)

    if assembly_missing:
        with open(assembly_outfile, 'w') as f:
            f.write(str(assembly_coverage))
        loggingC.message(f">Assembly coverage is {assembly_coverage}", threshold=0)
        loggingC.message(">Assembly coverage has been written to "
                         f"{os.path.abspath(assembly_outfile)}", threshold=0)

    if bins_required:
        loggingC.message(">Bin coverage file: "
                         f"{os.path.abspath(bin_coverage_file)}", threshold=0)

    return assembly_coverage, bin_coverage_file


def read_receipt(receipt_path: str) -> str:
    """
    Extract success status and appropriate accession (ANALYSIS or SAMPLE) from receipt file.
    
    Args:
        receipt_path (str): The path to the receipt file.
    """

    tree = ET.parse(receipt_path)
    root = tree.getroot()

    success = root.attrib['success']

    if success != 'true':
        err = format_receipt_failure(root, receipt_path, "sample")
        loggingC.message(err, threshold=-1)
        sys.exit(1)

    # Check for ANALYSIS receipt
    analysis_element = root.find('.//ANALYSIS')
    if analysis_element is not None:
        accession = analysis_element.attrib['accession']
        return accession

    # Check for SAMPLE receipt
    sample_element = root.find('.//SAMPLE')
    if sample_element is not None:
        accession = sample_element.attrib['accession']
        return accession

    # If neither, print error message
    loggingC.message(f"\nERROR: Unknown receipt type. Cannot extract accession.", threshold=-1)

    return None


def validate_parameter_combination(submit_samples: bool,
                                   submit_reads: bool,
                                   submit_assembly: bool,
                                   submit_bins: bool,
                                   submit_mags: bool,
                                   exit_on_invalid=True) -> bool:
    """
    Check if the parameters in their combination are valid. If not, fail
    gracefully.

    The following submission modes are valid:
     1.    Samples + Reads + Assembly + Bins + MAGs
     2.    Samples + Reads + Assembly + Bins
     3.    Samples + Reads + Assembly
     4.              Reads + Assembly + Bins + MAGs
     5.              Reads + Assembly + Bins
     6.              Reads + Assembly
     7.                      Assembly + Bins + MAGs
     8.                      Assembly + Bins
     9.                      Assembly
    10.                                 Bins + MAGs
    11.                                 Bins
    12.                                        MAGs
    13.    Samples
    14.              Reads
    15.    Samples + Reads

    Args:
        submit_samples (bool): Submit samples.
        submit_unpaired_reads (bool): Submit single reads.
        submit_paired_end_reads (bool): Submit paired-end reads.
        submit_assembly (bool): Submit assembly.
        submit_bins (bool): Submit bins.
        submit_mags (bool): Submit mags.
    """
    # Check if the user has specified a valid mode
    is_valid = False
    if ((submit_mags and not submit_bins) and (submit_samples or submit_reads or submit_assembly)): # MAGs can only be submitted with bins or alone
        is_valid = False
    elif (submit_samples and submit_reads and submit_assembly): # Mode 1-3
        is_valid = True
    elif (submit_reads and submit_assembly and not submit_samples): # Mode 4-6
        is_valid = True
    if (submit_assembly and submit_bins and not submit_samples and not submit_reads): # Mode 7-8
        is_valid = True
    elif (submit_assembly and not submit_bins and not submit_mags and not submit_samples and not submit_reads): # Mode 9
        is_valid = True
    if (submit_bins and submit_mags and not submit_assembly and not submit_samples and not submit_reads): # Mode 10
        is_valid = True 
    if ((submit_bins or submit_mags) and not submit_assembly and not submit_samples and not submit_reads): # Mode 11-12
        is_valid = True
    if ((submit_samples or submit_reads) and not submit_assembly and not submit_bins and not submit_mags): # Mode 13-14
        is_valid = True

    if not is_valid:
        if exit_on_invalid:
            # Dont use loggingC here, because this might be called from configGen
            print(f"\nERROR: The combination of parameters you have specified is not valid.")
            print(staticConfig.submission_modes_message)
            sys.exit(1)
        else:
            return False

    return True


def print_submission_schedule(submit_samples: bool,
                              submit_reads: bool,
                              submit_assembly: bool,
                              submit_bins: bool,
                              submit_mags: bool) -> bool:
    """
    Construct a string summarizing the submission schedule based on the
    parameters provided.

    Args:
        submit_samples (bool): Submit samples.
        submit_unpaired_reads (bool): Submit single reads.
        submit_paired_end_reads (bool): Submit paired-end reads.
        submit_assembly (bool): Submit assembly.
        submit_bins (bool): Submit bins.
        submit_mags (bool): Submit mags.

    Returns:
        str: The submission schedule.
    """
    counter = 1
    schedule = "Submission schedule:\n"
    if submit_samples:
        schedule += f"\t{counter}. Samples\n"
        counter += 1
    if submit_reads:
        schedule += f"\t{counter}. Reads\n"
        counter += 1
    if submit_assembly:
        schedule += f"\t{counter}. Assembly\n"
        counter += 1
    if submit_bins:
        schedule += f"\t{counter}. Bins\n"
        counter += 1
    if submit_mags:
        schedule += f"\t{counter}. MAGs\n"

    return schedule
