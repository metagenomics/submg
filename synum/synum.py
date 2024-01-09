#!/usr/bin/env python

import argparse
import os

import utility
from statConf import staticConfig

from tqdm import tqdm

from datetime import datetime
import time


from webinWrapper import find_webin_cli_jar
from assemblySubmission import submit_assembly
from binSubmission import submit_bins, get_bin_taxonomy, query_ena_taxonomy, get_bin_quality

from synum import staticConfig


def __check_date(date: str,
                 verbose: int = 1) -> None:
    """
    Check if the input is an ISO compliant date string.
    """
    valid_formats = [
        "%Y",              # Year only
        "%Y-%m",           # Year-month
        "%Y-%m-%d",        # Year-month-day
        "%Y-%m-%dT%H",     # Year-month-day hour
        "%Y-%m-%dT%H:%M",  # Year-month-day hour:minute
        "%Y-%m-%dT%H:%M:%S",  # Year-month-day hour:minute:second
    ]
    valid = False
    for fmt in valid_formats:
        try:
            # Try parsing with the current format
            datetime.strptime(date, fmt)
            valid = True
        except ValueError:
            continue

    if not valid:
        print(f"\nERROR: The date '{date}' is not a valid ISO date string.")
        exit(1)

def __check_config(args: argparse.Namespace,
                   config: dict,
                   verbose: int) -> None:
    
    if verbose>1:
        print(f">Checking config file at {args.config}")

    # Check if everything in the bins directory looks like a fasta file
    if args.submit_bins:
        bins_directory = utility.from_config(config, 'BINS', 'BINS_DIRECTORY')
        bin_files = os.listdir(bins_directory)
        for bin_file in bin_files:
            extension = '.' + bin_file.split('.')[-1]
            if not extension in staticConfig.fasta_extensions.split(';'):
                if verbose > -1:
                    print("#####")
                    print(f"WARNING: File {bin_file} in the bins directory does not end in {staticConfig.fasta_extensions} and will be skipped.")
                    print("#####")
    if args.submit_assembly:
        # Check if assembly fasta file looks correct
        fasta_path = utility.from_config(config, 'ASSEMBLY', 'FASTA_FILE')
        utility.check_fasta(fasta_path)
        # Is the molecule type valid?
        molecule_type = utility.from_config(config, 'ASSEMBLY', 'MOLECULE_TYPE')
        if not molecule_type in staticConfig.molecule_types:
            print(f"\nERROR: Molecule type '{molecule_type}' is not valid. Valid molecule types are: {', '.join(staticConfig.molecule_types)}")
            exit(1)
        if not molecule_type.startswith('genomic'):
            if verbose > -1:
                print("#####")
                print(f"WARNING: Molecule type is set to '{molecule_type}' - is this a mistake?")
                print("#####")
        # Is the assembly date valid?
        __check_date(utility.from_config(config, 'ASSEMBLY', 'DATE'), verbose)

    # Check if the assembly taxid is valid and matches the scientific name
    if args.submit_assembly:
        if verbose > 1:
            print(">Checking if assembly taxid is valid")
        assembly_taxid = utility.from_config(config, 'ASSEMBLY', 'TAXID')
        assembly_scientific_name = utility.from_config(config, 'ASSEMBLY', 'SPECIES_SCIENTIFIC_NAME')

        taxdata = query_ena_taxonomy(level="metagenome",
                                    domain="metagenome",
                                    classification=assembly_scientific_name,
                                    filtered=True,
                                    verbose=verbose)
        if len(taxdata) == 0 or len(taxdata) > 1:
            print(f"\nERROR: The scientific name '{assembly_scientific_name}' is not valid.")
            exit(1)
        taxdata = taxdata[0]
        if not taxdata['tax_id'] == assembly_taxid:
            print(f"\nERROR: The taxid '{assembly_taxid}' does not match the scientific name '{assembly_scientific_name}'.")
            exit(1)
        
    # Check if the BAM files exist and are indexed/sorted
    for bam_file in utility.from_config(config, 'BAM_FILES'):
        if not os.path.isfile(bam_file):
            print(f"\nERROR: BAM file {bam_file} does not exist.")
            exit(1)
        extension = '.' + bam_file.split('.')[-1]
        if not extension in staticConfig.bam_extensions.split(';'):
            print(f"\nERROR: BAM file {bam_file} has an invalid extension {extension}. Valid extensions are {staticConfig.bam_extensions}.")
            exit(1)

    # Query ENA to check if the various accessions (assembly, run_refs,
    # sample_refs) are valid
    # TODO

    # Test if the taxonomy files exist and look like taxonomy files.
    # TODO

    # Do the taxonomy files cover every bin in the bins directory?
    # TODO


def __construct_depth_files(args: argparse.Namespace,
                            config: dict,
                            verbose: int) -> dict:
    if verbose:
        print(f">Constructing depth files from bam files using {args.threads} threads. This might be stuck at 0% for a while.")
    depth_files = []
    depth_directory = os.path.join(args.staging_dir, 'depth')
    os.makedirs(depth_directory)
    bam_files = utility.from_config(config, 'BAM_FILES')
    if not type(bam_files) == list:
        bam_files = [bam_files]
    for bam_file in tqdm(bam_files, leave=False):
        depth_file = utility.make_depth_file(bam_file,
                                             depth_directory,
                                             num_threads=args.threads)
        depth_files.append(depth_file)
    return depth_files

def __preflight_checks(args: argparse.Namespace,
                       verbose: int) -> None:
    
    # Check if config file exists
    if not os.path.isfile(args.config):
        print(f"\nERROR: The config file '{args.config}' does not exist.")
        return
    
    # Read data from the YAML config file
    config = utility.read_yaml(args.config)

    # Do a superficial check of the config
    __check_config(args, config, verbose)

    # Check if webin-cli can be found
    if verbose>1:
        print(">Checking if webin-cli can be found")
    find_webin_cli_jar()

    # Check for login data
    utility.get_login()

    # Create staging dir if it doesn't exist
    if not os.path.exists(args.staging_dir):
        os.makedirs(args.staging_dir)

    # Check if staging dir is empty
    if os.listdir(args.staging_dir):
        print(f"\nERROR: Staging directory is not empty: {args.staging_dir}")
        exit(1)

    # Create logging dir if it doesn't exist
    if not os.path.exists(args.logging_dir):
        os.makedirs(args.logging_dir)

    # Check if logging dir is empty
    if os.listdir(args.logging_dir):
        print(f"\nERROR: Logging directory is not empty: {args.logging_dir}")
        exit(1)

    return config

def main():
    
    # Parsing command line input
    parser = argparse.ArgumentParser(description="""Tool for submitting metagenome bins to the European Nucleotide Archive.
                                     Environment variables ENA_USER and ENA_PASSWORD must be set for ENA upload.""")
    parser.add_argument("-x", "--config",           required=True,          help="Path to the YAML file containing metadata and filepaths. Mandatory")
    parser.add_argument("-s", "--staging_dir",      required=True,          help="Directory where files will be staged for upload. Must be empty. May use up a lot of disk space. Mandatory.")
    parser.add_argument("-l", "--logging_dir",      required=True,          help="Directory where log files will be stored. Must be empty. Mandatory.")
    parser.add_argument("-a", "--submit_assembly",  action="store_true",    help="Submit a primary metagenome assembly.")
    parser.add_argument("-b", "--submit_bins",      action="store_true",    help="Submit metagenome bins (note that bins are different from MAGs in the ENA definition).")
    parser.add_argument("-y", "--verbosity",        type=int, choices=[0, 1, 2], default=1, help="Control the amount of logging to stdout. [default 1]")
    parser.add_argument("-d", "--devtest",          type=int, choices=[0, 1], default=1, help="Make submissions to the ENA dev test server. [default 1/true]")
    parser.add_argument("-t", "--threads",          type=int, default=4, help="Number of threads used to process .bam files. [default 4]")
    parser.add_argument("-k", "--keep_depth_files", action="store_true",    help="Do not delete depth files after running. [default false]")
    parser.add_argument("-v", "--version",          action="version", version=f"%(prog)s {staticConfig.synum_version}")
    args = parser.parse_args()

    # Verbosity
    verbose = args.verbosity


    # Print version
    if verbose>0:
        print(f">Running synum version {staticConfig.synum_version}")
        if args.devtest == 1:
            print(">Making a test submission to the ENA dev server.")
        else:
            print(">Making a LIVE SUBMISSION to the ENA production server.")
            time.sleep(3)

    # Read in config and check if everything looks like we can start
    config = __preflight_checks(args, verbose)

    # If we are submitting bins, get the quality scores and the
    # taxonomic information.
    # We do this early so we notice issues before we start staging files.
    if args.submit_bins:
        # Get bin quality scores
        bin_quality = get_bin_quality(config, verbose=0)
        # Test if there are bins which are too contaminated
        for name in bin_quality.keys():
            contamination = bin_quality[name]['contamination']
            if contamination > staticConfig.max_contamination:
                print(f"\nERROR: Bin {name} has a contamination score of {contamination} which is higher than {staticConfig.max_contamination}")
                print(f"ENA will reject the submission of this bin. Consult the 'Contamination above 100%' of README.md for more information.")
                exit(1)
        # Query bin taxonomy
        bin_taxonomy = get_bin_taxonomy(config, verbose)
       
    # Construct depth files
    depth_files = __construct_depth_files(args, config, verbose)

   
    # Assembly submission
    if args.submit_assembly:
        submit_assembly(config,
                        args.staging_dir,
                        args.logging_dir,
                        depth_files,
                        threads=args.threads,
                        verbose=verbose)
        
    # Bin submission
    if args.submit_bins:
        submit_bins(config,
                    bin_taxonomy,
                    args.staging_dir,
                    args.logging_dir,
                    depth_files,
                    threads=args.threads,
                    verbose=verbose)

    print(">You will receive final accessions once your submission has been processed by ENA.")
    print(">ENA will send those final accession by email to the contact adress of your ENA account.")

    # Cleanup
    if not args.keep_depth_files:
        if verbose>0:
            print(">Deleting depth files to free up disk space.")
        for depth_file in depth_files:
            os.remove(depth_file)

if __name__ == "__main__":
    main()

