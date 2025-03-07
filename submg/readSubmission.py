import os
import csv

from submg.modules import loggingC, utility
from submg.modules.utility import from_config, stamped_from_config
from submg.modules.statConf import staticConfig
from submg.modules.webinWrapper import webin_cli

import shutil
import gzip

def __prep_reads_manifest(config: dict,
                          sample_accession_data,
                          data: dict,
                          staging_dir: str,
                          fastq1_path: str,
                          fastq2_path: str) -> str:
    """
    Prepare the manifest file for reads submission.

    Args:
        config (dict): The configuration dictionary.
        sample_accession_data (list): Contains one dictionary with information
            on each sample. Dict keys are 'accession', 'external_accession',
            and 'alias'.
        data (dict): dictionary containing the reads data.
        staging_dir (str): The directory where the reads are staged.
        fastq1_path (str): The path to the first fastq file.
        fastq2_path (str): The path to the second fastq file (if paired-end).
    """
    
    # Find the related sample
    if 'RELATED_SAMPLE_TITLE' in data.keys():
        sample_title = stamped_from_config(data, 'RELATED_SAMPLE_TITLE')
        sample = None
        for sd in sample_accession_data:
            if sd['alias'] == sample_title:
                sample = sd['accession']
                break
        if sample is None:
            err = f"\nERROR: No related sample found for the reads with title '{sample_title}'. Please check the configuration file."
            loggingC.message(err, threshold=-1)
            exit(1)
    elif 'RELATED_SAMPLE_ACCESSION' in data.keys():
        sample = from_config(data, 'RELATED_SAMPLE_ACCESSION')
    else:
        err = "\nERROR: No related sample found for the reads. Please specify either 'RELATED_SAMPLE_TITLE' or 'RELATED_SAMPLE_ACCESSION' in the configuration file."
        loggingC.message(err, threshold=-1)

    # Build the rows
    rows = [
        ['STUDY', from_config(config, 'STUDY')],
        ['SAMPLE', sample],
        ['NAME', stamped_from_config(data, 'NAME')],
        ['INSTRUMENT', from_config(data, 'SEQUENCING_INSTRUMENT')],
        ['LIBRARY_SOURCE', from_config(data, 'LIBRARY_SOURCE')],
        ['LIBRARY_SELECTION', from_config(data, 'LIBRARY_SELECTION')],
        ['LIBRARY_STRATEGY', from_config(data, 'LIBRARY_STRATEGY')],
    ]

    if 'FASTQ_FILE' in data: # Single-end reads
        rows.append(['FASTQ', os.path.basename(fastq1_path)])
    else: # Paired-end reads
        rows.append(['INSERT_SIZE', from_config(data, 'INSERT_SIZE')])
        rows.append(['FASTQ', os.path.basename(fastq1_path)])
        rows.append(['FASTQ', os.path.basename(fastq2_path)])

    if 'ADDITIONAL_MANIFEST_FIELDS' in data.keys() and data['ADDITIONAL_MANIFEST_FIELDS'] is not None:
        for key, value in data['ADDITIONAL_MANIFEST_FIELDS'].items():
            rows.append([key, value])

    # Write the manifest
    manifest_path = os.path.join(staging_dir, 'MANIFEST')
    with open(manifest_path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    return manifest_path


def __zipcopy(input: str,
              output: str) -> None:
    """
    Copy a file, compressing it if the input file does not have a '.gz' extension.

    Args:
        input (str): The path to the input file.
        output (str): The path to the output file.
    """
    if input.endswith('gz'):
        shutil.copyfile(input, output)
    else:
        with open(input, 'rb') as f_in:
            with gzip.open(output, 'wb', compresslevel=5) as f_out:
                f_out.writelines(f_in)


def __stage_reads_submission(config: dict,
                             sample_accession_data,
                             data: dict,
                             staging_dir: str,
                             logging_dir: str) -> str:
    """
    Stage the reads for submission.

    Args:
        config (dict): The configuration dictionary.
        sample_accession_data (list): Contains one dictionary with information
            on each sample. Dict keys are 'accession', 'external_accession',
            and 'alias'.
        data (dict): dictionary containing the reads data.
        staging_dir (str): The directory where the reads will be staged.
        logging_dir (str): The directory where the submission logs will be
            written.

    Returns:
        str: The path to the manifest file.
    """
    # Stage the fastq file(s)
    gzipped_fastq1_path = os.path.join(staging_dir, 'reads_1' + staticConfig.zipped_fastq_extension)
    gzipped_fastq2_path = os.path.join(staging_dir, 'reads_2' + staticConfig.zipped_fastq_extension)
    if 'FASTQ_FILE' in data: # Single-end reads
        fastq1_path = from_config(data, 'FASTQ_FILE')
        fastq2_path = None
    else: # Paired-end reads
        fastq1_path = from_config(data, 'FASTQ1_FILE')
        fastq2_path = from_config(data, 'FASTQ2_FILE')
    __zipcopy(fastq1_path, gzipped_fastq1_path)
    if not fastq2_path is None:
        __zipcopy(fastq2_path, gzipped_fastq2_path)

    # Make the MANIFEST file
    manifest = __prep_reads_manifest(config,
                                     sample_accession_data,
                                     data,
                                     staging_dir,
                                     gzipped_fastq1_path,
                                     gzipped_fastq2_path)
    return manifest
    

def submit_reads(config,
                 sample_accession_data,
                 staging_dir,
                 logging_dir,
                 test=True,
                 minitest=False):
    """
    Submits the specified reads to ENA.

    Args:
        config (dict): The configuration dictionary.
        sample_accession_data (list): Contains one dictionary with information
            on each sample. Dict keys are 'accession', 'external_accession',
            and 'alias'.
        staging_dir (str): The directory where the reads will be staged.
        logging_dir (str): The directory where the submission logs will be
            written.
        test (bool, optional): If True, use the Webin test submission service
        (default is True).

    Returns:
        list: The accessions of the submitted reads.
    """
    read_manifests = {}

    counter = 0
    if 'PAIRED_END_READS' in config.keys():
        loggingC.message(">Staging paired-end reads for submission. This might take a while.", threshold=0)
        for i, data in enumerate(from_config(config, 'PAIRED_END_READS')):
            name = stamped_from_config(data, 'NAME').replace(' ', '_')
            read_set_staging_dir = os.path.join(staging_dir, f"reads_{name}")
            os.makedirs(read_set_staging_dir, exist_ok=False)
            read_set_logging_dir = os.path.join(logging_dir, f"reads_{name}")
            os.makedirs(read_set_logging_dir, exist_ok=False)
            manifest = __stage_reads_submission(config,
                                                sample_accession_data,
                                                data,
                                                read_set_staging_dir,
                                                read_set_logging_dir)                                                
            if not name in read_manifests:
                read_manifests[name] = manifest  
            counter = i + 1
            if minitest:
                msg = ">Minitest: Only submitting the first paired-end read set."
                loggingC.message(msg, threshold=0)
                break

    if 'SINGLE_READS' in config.keys():
        loggingC.message(">Staging single-end reads for submission. This might take a while.", threshold=0)
        for j, data in enumerate(from_config(config, 'SINGLE_READS')):
            i = counter + j
            name = stamped_from_config(data, 'NAME').replace(' ', '_')
            read_set_staging_dir = os.path.join(staging_dir, f"reads_{name}")
            os.makedirs(read_set_staging_dir, exist_ok=False)
            read_set_logging_dir = os.path.join(logging_dir, f"reads_{name}")
            os.makedirs(read_set_logging_dir, exist_ok=False)
            manifest = __stage_reads_submission(config,
                                                sample_accession_data,
                                                data,
                                                read_set_staging_dir,
                                                read_set_logging_dir)         
            
            if not name in read_manifests:
                read_manifests[name] = manifest    
            if minitest:
                msg = ">Minitest: Only submitting the first single-end read set."
                loggingC.message(msg, threshold=0)
                break                                

    # Upload the reads
    loggingC.message(f">Using ENA Webin-CLI to submit reads.", threshold=0)
    usr, pwd = utility.get_login()
    read_receipts = {}
    read_accessions = {}
    for name, manifest in read_manifests.items():
        loggingC.message(f">Submitting file at {manifest}", threshold=2)
        read_set_logging_dir = os.path.join(logging_dir, f"reads_{name}")

        read_receipts[name], read_accessions[name] = webin_cli(manifest=manifest,
                                                               inputdir=os.path.dirname(manifest),
                                                               outputdir=read_set_logging_dir,
                                                               username=usr,
                                                               password=pwd,
                                                               subdir_name=name,
                                                               submit=True,
                                                               test=test,
                                                               context='reads')
        
    loggingC.message("\n>Read submission completed!", threshold=0)
    loggingC.message(">Read receipt paths are:", threshold=1)
    for name, receipt in read_receipts.items():
        loggingC.message(f"\t{name}: {os.path.abspath(receipt)}", threshold=1)

    read_to_accession_file = os.path.join(logging_dir, 'readset_to_preliminary_accession.tsv')
    with open(read_to_accession_file, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for name, accession in read_accessions.items():
            writer.writerow([name, accession])


    loggingC.message(f"\n>The preliminary(!) accessions of your reads have been written to {os.path.abspath(read_to_accession_file)}.\n", threshold=0)
      

    return list(read_accessions.values())