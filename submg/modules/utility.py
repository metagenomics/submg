import os
import csv
import yaml
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
from tqdm import tqdm
from yaspin import yaspin

from . import loggingC
from .statConf import staticConfig


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
    global USE_GUI, gui_credentials
    USE_GUI = True
    gui_credentials["username"] = username
    gui_credentials["password"] = password


def full_timestamp():
    """
    Creates and returns a full timestamp (year, month, day, hour, minute, second).
    """
    return time.strftime("%Y%m%d%H%M%S")


def set_up_timestamps(arguments: dict):
    """
    Set up the timestamp for the submission. Data is only timestamped with
    the hour and minute. Because of daily resets, this is sufficient to
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
    timestamp = time.strftime("%H%M")


def construct_depth_files(staging_dir: str,
                          threads: int,
                          bam_files: list) -> dict:
    """
    Construct depth files from bam files.

    Args:
        staging_dir: The staging directory.
        threads: The total number of threads to use.
        bam_files: The list of bam files.
    """
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


def api_response_check(response: requests.Response):
    if response.status_code == 403:
        err = """\nERROR: Submission failed. ENA API returned status code 403.
                    This indicates incorrect ENA login credentials. Please test your credentials
                    by logging in to the ENA submission web interface. Make sure the environment variables
                    ENA_USER and ENA_PASSWORD contain these credentials."""
        loggingC.message(err, threshold=-1)
        exit(1)

    if response.status_code == 400:
        err = "\nERROR: Submission failed. ENA API returned status code 400. This indicates a bad request."
        loggingC.message(err, threshold=-1)
        exit(1)

    if response.status_code == 408:
        err = "\nERROR: Submission failed. ENA API returned status code 408. This indicates a timeout."
        loggingC.message(err, threshold=-1)
        exit(1)

    if response.status_code != 200:
        err = f"\nERROR: Submission failed. ENA API returned status code {response.status_code}."
        loggingC.message(err, threshold=-1)
        exit(1)

    if response.text == "":
        err = "\nERROR: Submission failed, received an empty response from API endpoint."
        loggingC.message(err, threshold=-1)
        exit(1)


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
    global USE_GUI, gui_credentials

    if USE_GUI:
        if gui_credentials["username"] is None or gui_credentials["password"] is None:
            err = "\nERROR: GUI credentials not set."
            loggingC.message(err, threshold=-1)
            exit(1)
        return gui_credentials["username"], gui_credentials["password"]
    
    # Fallback to environment variables for CLI usage
    if 'ENA_USER' not in os.environ:
        err = "\nERROR: ENA_USER environmental variable not set. Please export your ENA username as ENA_USER."
        loggingC.message(err, threshold=-1)
        exit(1)
    if 'ENA_PASSWORD' not in os.environ:
        err = "\nERROR: ENA_PASSWORD environmental variable not set. Please export your ENA password as ENA_PASSWORD."
        loggingC.message(err, threshold=-1)
        exit(1)

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

    try:
        with open(file_path, 'r') as yaml_file:
            data = yaml.safe_load(yaml_file)
            if convert_file_paths:
                base_path = os.path.dirname(os.path.abspath(file_path))
                data = convert_paths(data, base_path)
            return data
    except FileNotFoundError:
        err = f"\nERROR: YAML file not found at: {file_path}"
        loggingC.message(err, threshold=-1)
        exit(1)
    except Exception as e:
        err = f"\nERROR: An error occurred while reading {file_path}, error is:\n{e}"
        loggingC.message(err, threshold=-1)
        exit(1)


def read_yaml(file_path, convert_file_paths=True):
    """ 
    Reads a YAML file and returns the data as a dictionary.

    Args:
        file_path (str): The path to the YAML file.
        convert_file_paths (bool): If True, file paths will be converted to
                                   absolute paths.
    """
    try:
        with open(file_path, 'r') as yaml_file:
            data = yaml.safe_load(yaml_file)
            return data
    except FileNotFoundError:
        err = f"\nERROR: YAML file not found at: {file_path}"
        loggingC.message(err, threshold=-1)
        exit(1)
    except Exception as e:
        err = f"\nERROR: An error occurred while reading {file_path}, error is:\n{e}"
        loggingC.message(err, threshold=-1)
        exit(1)


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
        exit(1)
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
            exit(1)
        else:
            return None
    if not config[key]:
        if not supress_errors:
            err = f"\nERROR: The field '{key}' is empty in the config YAML file."
            loggingC.message(err, threshold=-1)
            exit(1)
        else:
            return None
    if subkey:
        if not subkey in config[key]:
            if not supress_errors:
                err = f"\nERROR: The field '{key}|{subkey}' is missing from the config YAML file."
                loggingC.message(err, threshold=-1)
                exit(1)
            else:
                return None
        if not config[key][subkey]:
            if not supress_errors:
                err = f"\nERROR: The field '{key}|{subkey}' is empty in the config YAML file."
                loggingC.message(err, threshold=-1)
                exit(1)
        if subsubkey:
            if not subsubkey in config[key][subkey]:
                if not supress_errors:
                    err = f"\nERROR: The field '{key}|{subkey}|{subsubkey}' is missing from the config YAML file."
                    loggingC.message(err, threshold=-1)
                    exit(1)
                else:
                    return None
            if not config[key][subkey][subsubkey]:
                if not supress_errors:
                    err = f"\nERROR: The field '{key}|{subkey}|{subsubkey}' is empty in the config YAML file."
                    loggingC.message(err, threshold=-1)
                    exit(1)
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
                exit(1)
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
                exit(1)
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
    global timestamp
    global keys_to_stamp
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
    if fastq_filepath.endswith('.gz'):
        fastq_filepath = fastq_filepath[:-3]
    if not os.path.isfile(fastq_filepath):
        err = f"\nERROR: The FASTQ file '{fastq_filepath}' does not exist."
        loggingC.message(err, threshold=-1)
        exit(1)
    extensions = staticConfig.fastq_extensions.split(';')
    if not fastq_filepath.endswith(tuple(extensions)):
        err = f"\nERROR: The FASTQ file '{fastq_filepath}' has an invalid extension. Valid extensions are {'|'.join(extensions)}."
        loggingC.message(err, threshold=-1)
        exit(1)
        

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
    if filepath.endswith('.gz'):
        filepath = filepath[:-3]
    if not filepath.endswith(tuple(extensions)):
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
        exit(1)
    elif not os.path.isfile(fasta_path):
        err = f"\nERROR: Trying to submit assembly, but the FASTA file {fasta_path} does not exist."
        loggingC.message(err, threshold=-1)
        exit(1)
    extension = fasta_path.split('.')[-1]
    gzipped = False
    if extension == 'gz':
        gzipped = True
        extension = fasta_path.split('.')[-2]
    if not extension in staticConfig.fasta_extensions:
        err = f"\nERROR: fasta file at {fasta_path} has an unknown file extension ({extension}). Allowed extensions are {staticConfig.fasta_extensions} (+.gz)."
        loggingC.message(err, threshold=-1)
        exit(1)
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
        min_completeness = config['BINS']['MIN_COMPLETENESS']
        msg = f">Filtering bins based on minimum completeness of {min_completeness}."
    else:
        min_completeness = 0
        msg = ">No MIN_COMPLETENESS specified, bins will not be filtered for completeness."
    loggingC.message(msg, threshold=0)
    if 'MAX_CONTAMINATION' in config['BINS']:
        max_contamination = config['BINS']['MAX_CONTAMINATION']
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
        exit(1)
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
        exit(1)

    # Check if the ending of the file is .bam or .BAM
    if bam_file.endswith('.BAM'):
        file_ending = '.BAM'
    elif bam_file.endswith('.bam'):
        file_ending = '.bam'
    else:
        ext = bam_file.split('.')[-1]
        err = f"\nERROR: The file {bam_file} has the unexpected extension {ext} (expected .bam or .BAM)."
        loggingC.message(err, threshold=-1)
        exit(1)

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
        exit(1)
    sorted_bam_file = check_bam(bam_file, num_threads=num_threads)
    filename = os.path.basename(sorted_bam_file) + '.depth'
    outfile = os.path.join(outdir, filename)
    pysam.depth("-@", str(num_threads), "-a", sorted_bam_file, "-o", outfile)
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


def calculate_coverage(depth_files: list,
                       target_contigs: set = None,
                       threads=4,
                       outfile=None,
                       silent=False):
    """
    Calculate the average coverage of an assembly based on multiple depth files using parallel processing.

    Args:
    depth_files (list of str): List of file paths to depth files.
    target_contigs (set of str): Set of contigs to calculate coverage for.

    Returns:
    float: Average depth of coverage of the assembly.
    """
    total_coverage = 0.0
    total_length = 0.0

    def process_file(depth_file):
        """
        Process a single depth file and calculate coverage and length.
        """
        with open(depth_file, 'r') as depth:
            local_coverage = 0
            local_length = 0
            contig_coverage, contig_length = contigs_coverage(depth)
            for contig in contig_coverage:
                if target_contigs is not None:
                    if not contig in target_contigs:
                        continue
                local_coverage += contig_coverage[contig]
                local_length += contig_length[contig]
            return local_coverage, local_length

    if silent:
        threshold = 3
    else:
        threshold = 0
    loggingC.message(">Calculating coverage from depth files. This might take a while.", threshold)
    msg = f">The coverage value will be written to {outfile} in case you " \
            " want to provide a KNOWN_COVERAGE in the ASSEMBLY section " \
            " in the config for subsequent submission attempts."
    if outfile:
        loggingC.message(msg, threshold=0)

    inuse = min(threads, len(depth_files))
    with yaspin(text=f"Processing with {inuse} threads...\t", color="yellow") as spinner:
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            results = executor.map(process_file, depth_files)

        for coverage, length in results:
            total_coverage += coverage
            total_length += length

        average_coverage = total_coverage / total_length if total_length > 0 else 0

    if not silent:
        loggingC.message(f"\t...coverage is {str(average_coverage)}", threshold=0)

    if outfile:
        with open(outfile, 'w') as f:
            f.write(str(average_coverage))

    return average_coverage


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
        err = f"\nERROR: Submission failed. Please consult the receipt file at {os.path.abspath(receipt_path)} for more information."
        loggingC.message(err, threshold=-1)
        exit(1)

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
        submit_single_reads (bool): Submit single reads.
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
            exit(1)
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
        submit_single_reads (bool): Submit single reads.
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
