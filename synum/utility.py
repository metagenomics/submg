import os
import csv
import yaml
import pysam
import time
import requests
import hashlib
import xml.etree.ElementTree as ET
import concurrent.futures
from tqdm import tqdm
from yaspin import yaspin

from synum import loggingC
from synum.statConf import staticConfig


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

# def construct_depth_files(staging_dir: str,
#                           threads: int,
#                           config: dict) -> dict:
#     """
#     Construct depth files from bam files.

#     Args:
#         staging_dir: The staging directory.
#         threads: The number of threads to use.
#         config:  The config file as a dictionary.
#     """
#     loggingC.message(f">Constructing depth files from bam files using {threads} threads. This might be stuck at 0% for a while.", threshold=0)
#     depth_files = []
#     depth_directory = os.path.join(staging_dir, 'depth')
#     os.makedirs(depth_directory)
#     bam_files = from_config(config, 'BAM_FILES')
#     if not type(bam_files) == list:
#         bam_files = [bam_files]
#     for bam_file in tqdm(bam_files, leave=False):
#         depth_file = make_depth_file(bam_file,
#                                              depth_directory,
#                                              num_threads=threads)
#         depth_files.append(depth_file)
#     return depth_files

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
    ET.indent(tree, space="\t", level=0)

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
    Reads ENA login credentials from environmental variables and returns them.
    """
    if not 'ENA_USER' in os.environ:
        err = "\nERROR: ENA_USER environmental variable not set. Please export your ENA username and password as environmental variables ENA_USER and ENA_PASSWORD."
        loggingC.message(err, threshold=-1)
        exit(1)
    if not 'ENA_PASSWORD' in os.environ:
        err = "\nERROR: ENA_PASSWORD environmental variable not set. Please export your ENA username and password as environmental variables ENA_USER and ENA_PASSWORD."
        loggingC.message(err, threshold=-1)
        exit(1)
    return os.environ['ENA_USER'], os.environ['ENA_PASSWORD']

def read_yaml(file_path):
    try:
        with open(file_path, 'r') as yaml_file:
            data = yaml.safe_load(yaml_file)
            return data
    except FileNotFoundError:
        err = f"\nERROR: YAML file not found at: {file_path}"
        loggingC.message(err, threshold=-1)
        exit(1)
    except Exception as e:
        err = f"\nERROR: An error occurred while reading {file_path}, error is: {e}"
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

    
def from_config(config, key, subkey=None, subsubkey=None, supress_errors=False):
    """
    Extracts a value from the dict that was created based on the
    config YAML file.
    """
    if not key in config:
        if not supress_errors:
            err = f"\nERROR: The field '{key}' is missing from the config YAML file."
            loggingC.message(err, threshold=-1)
            exit(1)
    if not config[key]:
        if not supress_errors:
            err = f"\nERROR: The field '{key}' is empty in the config YAML file."
            loggingC.message(err, threshold=-1)
            exit(1)
    if subkey:
        if not subkey in config[key]:
            if not supress_errors:
                err = f"\nERROR: The field '{key}|{subkey}' is missing from the config YAML file."
                loggingC.message(err, threshold=-1)
                exit(1)
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
            if not config[key][subkey][subsubkey]:
                if not supress_errors:
                    err = f"\nERROR: The field '{key}|{subkey}|{subsubkey}' is empty in the config YAML file."
                    loggingC.message(err, threshold=-1)
                    exit(1)
            return __strcast(config[key][subkey][subsubkey])
        return __strcast(config[key][subkey])
    return __strcast(config[key])

def optional_from_config(config, key, subkey=None):
    if not key in config:
        return ''
    if not config[key]:
        return ''
    if subkey:
        if not subkey in config[key]:
            return ''
        if not config[key][subkey]:
            return ''
        return config[key][subkey]
    return config[key]

# def calculate_assembly_length(fasta_file):
#     """
#     Calculate the total length of the assembly from a FASTA file.

#     Args:
#     fasta_file (str): File path to the FASTA file. Can be gzipped.

#     Returns:
#     int: Total length of the assembly.
#     """
#     total_length = 0
#     with pysam.FastaFile(fasta_file) as fasta:
#         for seq in fasta.references:
#             total_length += fasta.get_reference_length(seq)

#     return total_length

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


    inuse = min(threads, len(depth_files))
    with yaspin(text=f"Processing with {inuse} threads...\t", color="yellow") as spinner:
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            results = executor.map(process_file, depth_files)

        for coverage, length in results:
            total_coverage += coverage
            total_length += length

        average_coverage = total_coverage / total_length if total_length > 0 else 0

    if not silent:
        loggingC.message(f"\t...coverage is {str(average_coverage)}", threshold+1)

    return average_coverage

# def calculate_coverage(depth_files: list,
#                        target_contigs: str = None,
#                        threads=4):
#     """
#     Calculate the average coverage of an assembly based on multiple depth files.

#     Args:
#     depth_files (list of str): List of file paths to depth files.
#     target_contigs (list of str): List of contigs to calculate coverage for.

#     Returns:
#     float: Average depth of coverage of the assembly.
#     """
#     total_coverage = 0.0
#     total_length = 0.0

#     loggingC.message(">Calculating coverage from depth files. This might take a while.", threshold=0)

#     for depth_file in tqdm(depth_files, leave=False):
#         with open(depth_file, 'r') as depth:
#             contig_coverage, contig_length = contigs_coverage(depth)
#             for contig in contig_coverage:
#                 if target_contigs is not None:
#                     if not contig in target_contigs:
#                         continue
#                 total_coverage += contig_coverage[contig]
#                 total_length += contig_length[contig]

#     average_coverage = total_coverage / total_length

#     loggingC.message(f"\t...all depth files processed, coverage is {str(average_coverage)}", threshold=0)

#     return average_coverage

'''
def calculate_coverage(bam_files, fasta_file, num_threads=4):
    """
    Calculate the average coverage of an assembly based on multiple .BAM files.

    Args:
    bam_files (list of str): List of file paths to .BAM files.
    fasta_file (str): File path to the FASTA file for the assembly.

    Returns:
    float: Average depth of coverage of the assembly.
    """
    assembly_length = calculate_assembly_length(fasta_file)
    total_coverage = 0.0
    print(">Trying to calculate coverage (might be stuck at 0% for a long time)")

    with yaspin(text=" ", color="yellow", spinner="dots") as spinner:
        counter = -1
        for bam_file in bam_files:
            counter += 1
            spinner.text = f"\t\t{counter} of {len(bam_files)} .bam files processed.   "
            # Check the file ending
            if bam_file.endswith('.BAM'):   
                file_ending = '.BAM'
            elif bam_file.endswith('.bam'):
                file_ending = '.bam'
            else:
                ext = bam_file.split('.')[-1]
                print(f"\nERROR: The file {bam_file} has the unexpected extension {ext} (expected .bam or .BAM).   ")
                exit(1)

            # Check if BAM file is sorted, sort it if not
            sorted_bam_file = bam_file
            try:
                pysam.index(sorted_bam_file, "-@", str(num_threads))
            except: # This might mean the bam file is not sorted, so we try that
                time.sleep(1)
                print(f"Error: Cannot read {bam_file}. The file might be unsorted, trying to sort...")
                sorted_bam_file = bam_file.replace(file_ending, '.tmp.sorted'+file_ending)
                pysam.sort("-o", sorted_bam_file, bam_file, "-@", str(num_threads))
                time.sleep(1)
                pysam.index(sorted_bam_file)
                time.sleep(1)                

            with pysam.AlignmentFile(sorted_bam_file, "rb") as bam:
                for read in bam.fetch():
                    if not read.is_unmapped:
                        total_coverage += read.reference_length

        counter += 1             
        spinner.text = f"\t\t{counter} of {len(bam_files)} .bam files processed.   "
    
    average_coverage = total_coverage / assembly_length
    print(f"\t...all bam files processed, coverage is {str(average_coverage)}")
    return average_coverage
'''


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