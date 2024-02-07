import os
import csv

from synum import loggingC, utility
from synum.utility import from_config
from synum.statConf import staticConfig
from synum.webinWrapper import webin_cli

import shutil
import gzip

def __prep_reads_manifest(config: dict,
                          data: dict,
                          staging_dir: str,
                          fastq1_path: str,
                          fastq2_path: str) -> str:
    
    # Find the related sample
    if 'RELATED_SAMPLE_TITLE' in data.keys():
        sample = from_config(data, 'RELATED_SAMPLE_TITLE')
    elif 'RELATED_SAMPLE_ACCESSION' in data.keys():
        sample = from_config(data, 'RELATED_SAMPLE_ACCESSION')

    # Build the rows
    rows = [
        ['STUDY', from_config(config, 'STUDY')],
        ['SAMPLE', sample],
        ['NAME', from_config(data, 'NAME')],
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
                             data: dict,
                             staging_dir: str,
                             logging_dir: str) -> str:
    """
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
                                     data,
                                     staging_dir,
                                     gzipped_fastq1_path,
                                     gzipped_fastq2_path)
    return manifest
    

def submit_reads(config,
                 staging_dir,
                 logging_dir,
                 test=True):
    """
    Submits the specified reads to ENA.

    Args:
        config (dict): The configuration dictionary.
        staging_dir (str): The directory where the reads will be staged.
        logging_dir (str): The directory where the submission logs will be written.
        test (bool, optional): If True, use the Webin test submission service (default is True).

    Returns:
        list: The accessions of the submitted reads.
    """
    read_manifests = {}

    counter = 0
    if 'PAIRED_END_READS' in config.keys():
        loggingC.message(">Staging paired-end reads for submission. This might take a while.", threshold=0)
        for i, data in enumerate(from_config(config, 'PAIRED_END_READS')):
            name = from_config(data, 'NAME').replace(' ', '_')
            read_set_staging_dir = os.path.join(staging_dir, f"reads_{name}")
            os.makedirs(read_set_staging_dir, exist_ok=False)
            read_set_logging_dir = os.path.join(logging_dir, f"reads_{name}")
            os.makedirs(read_set_logging_dir, exist_ok=False)
            manifest = __stage_reads_submission(config,
                                                data,
                                                read_set_staging_dir,
                                                read_set_logging_dir)                                                
            if not name in read_manifests:
                read_manifests[name] = manifest  
            counter = i + 1

    if 'SINGLE_END_READS' in config.keys():
        loggingC.message(">Staging single-end reads for submission. This might take a while.", threshold=0)
        for j, data in enumerate(from_config(config, 'SINGLE_END_READS')):
            i = counter + j
            name = from_config(data, 'NAME').replace(' ', '_')
            read_set_staging_dir = os.path.join(staging_dir, f"reads_{name}")
            os.makedirs(read_set_staging_dir, exist_ok=False)
            read_set_logging_dir = os.path.join(logging_dir, f"reads_{name}")
            os.makedirs(read_set_logging_dir, exist_ok=False)
            manifest = __stage_reads_submission(config,
                                                data,
                                                read_set_staging_dir,
                                                read_set_logging_dir)         
            
            if not name in read_manifests:
                read_manifests[name] = manifest                                       

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

    read_to_accession_file = os.path.join(logging_dir, 'read_to_preliminary_accession.tsv')
    with open(read_to_accession_file, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for name, accession in read_accessions.items():
            writer.writerow([name, accession])


    loggingC.message(f"\n>The preliminary(!) accessions of your reads have been written to {os.path.abspath(read_to_accession_file)}.\n", threshold=0)
      

    return list(read_accessions.values())