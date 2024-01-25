import os
import argparse

from datetime import datetime

from synum import loggingC, utility
from synum.statConf import staticConfig
from synum.webinWrapper import find_webin_cli_jar
from synum.binSubmission import query_ena_taxonomy

def __check_date(date: str) -> None:
    """
    Check if the input is an ISO compliant date string.

    Args:
        date:    The date string to check.

    Raises:

    """
    valid_formats = [
        "%Y",                   # Year only
        "%Y-%m",                # Year-month
        "%Y-%m-%d",             # Year-month-day
        "%Y-%m-%dT%H",          # Year-month-day hour
        "%Y-%m-%dT%H:%M",       # Year-month-day hour:minute
        "%Y-%m-%dT%H:%M:%S",    # Year-month-day hour:minute:second
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
        err = f"\nERROR: The date '{date}' is not a valid ISO date string."
        loggingC.message(err, threshold=-1)
        exit(1)

def __check_config(args: argparse.Namespace,
                   config: dict) -> None:
    """
    Does a superficial check of the config file.

    Args:
        args:    The command line arguments.
        config:  The config file as a dictionary.
    """
    return # THIS NEEDS TO BE REWORKED
    loggingC.message(f">Checking config file at {args.config}", threshold=1)

    # Check if everything in the bins directory looks like a fasta file
    if args.submit_bins:
        bins_directory = utility.from_config(config, 'BINS', 'BINS_DIRECTORY')
        bin_files = os.listdir(bins_directory)
        for bin_file in bin_files:
            extension = '.' + bin_file.split('.')[-1]
            if not extension in staticConfig.fasta_extensions.split(';'):
                loggingC.message(f"WARNING: File {bin_file} in the bins directory does not end in {staticConfig.fasta_extensions} and will be skipped.", threshold=-1)
    if args.submit_assembly:
        # Check if assembly fasta file looks correct
        fasta_path = utility.from_config(config, 'ASSEMBLY', 'FASTA_FILE')
        utility.check_fasta(fasta_path)
        ## Is the molecule type valid?
        #molecule_type = utility.from_config(config, 'ASSEMBLY', 'MOLECULE_TYPE')
        #if not molecule_type in staticConfig.molecule_types:
        #    print(f"\nERROR: Molecule type '{molecule_type}' is not valid. Valid molecule types are: {', '.join(staticConfig.molecule_types)}")
        #    exit(1)
        #if not molecule_type.startswith('genomic'):
        #loggingC.message(f"WARNING: Molecule type is set to '{molecule_type}' - is this a mistake?", threshold=0)

        
        ## Is the assembly date valid?
        #__check_date(utility.from_config(config, 'ASSEMBLY', 'DATE'))

    # Check if the assembly taxid is valid and matches the scientific name
    if args.submit_assembly:
        loggingC.message(f">Checking if assembly taxid is valid", threshold=1)
        assembly_taxid = utility.from_config(config, 'ASSEMBLY', 'TAXID')
        assembly_scientific_name = utility.from_config(config, 'ASSEMBLY', 'SPECIES_SCIENTIFIC_NAME')

        taxdata = query_ena_taxonomy(level="metagenome",
                                    domain="metagenome",
                                    classification=assembly_scientific_name,
                                    filtered=True)
        if len(taxdata) == 0 or len(taxdata) > 1:
            err = f"\nERROR: The scientific name '{assembly_scientific_name}' is not valid."
            loggingC.message(err, threshold=-1)
            exit(1)
        taxdata = taxdata[0]
        if not taxdata['tax_id'] == assembly_taxid:
            err = f"\nERROR: The taxid '{assembly_taxid}' does not match the scientific name '{assembly_scientific_name}'."
            loggingC.message(err, threshold=-1)
            exit(1)
        
    # Check if the BAM files exist and are indexed/sorted
    for bam_file in utility.from_config(config, 'BAM_FILES'):
        if not os.path.isfile(bam_file):
            err = f"\nERROR: BAM file {bam_file} does not exist."
            loggingC.message(err, threshold=-1)
            exit(1)
        extension = '.' + bam_file.split('.')[-1]
        if not extension in staticConfig.bam_extensions.split(';'):
            err = f"\nERROR: BAM file {bam_file} has an invalid extension {extension}. Valid extensions are {staticConfig.bam_extensions}."
            loggingC.message(err, threshold=-1)
            exit(1)

    # Query ENA to check if the various accessions (assembly, run_refs,
    # sample_refs) are valid
    # TODO

    # Test if the taxonomy files exist and look like taxonomy files.
    # TODO

    # Do the taxonomy files cover every bin in the bins directory?
    # TODO
            
    # Are the read files gzipped fastq?
    # TODO
            
    # If --submit_reads, is all the required data present?
    # TODO
    # And are the fields with controlled vocabularies valid?
    # TODO
    # The different read sets must have unique names
    # TODO
            
    # If --submit_samples, is all the required data present?
    # TODO

    # If are not submitting an assembly, can we query the neccessary data?
            
    # Passen die Assembly accessions? siehe diese message
    print("""\nSince you chose not to submit an assembly, we assume that it is
          already present in the ENA database. If this previously submitted
          assembly is a co-assembly, fill out the field
          \tEXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION
          in the config file. If the assembly is based on a single sample,
          fill out the field
          \tEXISTING_ASSEMBLY_ANALYSIS_ACCESSION
          in the config file.
          Only fill out one of these fields an leave the other empty.""")
            
    # The logging dir CANNOT be the same as the staging dir
    if args.logging_dir == args.staging_dir:
        err = f"\nERROR: The logging directory cannot be the same as the staging directory."
        loggingC.message(err, threshold=-1)
        exit(1)
            


def preflight_checks(args: argparse.Namespace) -> None:
    """
    Check if everything looks like we can start.

    Args:
        args:    The command line arguments.

    Returns:
        The config file as a dictionary.
    """
    # Check if config file exists
    if not os.path.isfile(args.config):
        err = f"\nERROR: The config file '{args.config}' does not exist."
        loggingC.message(err, threshold=-1)
        exit(1)
    
    # Read data from the YAML config file
    config = utility.read_yaml(args.config)

    # Do a superficial check of the config
    __check_config(args, config)

    # Check if webin-cli can be found
    loggingC.message(f">Checking if webin-cli can be found", threshold=1)
    find_webin_cli_jar()

    # Check for login data
    utility.get_login()

    # Create staging dir if it doesn't exist
    if not os.path.exists(args.staging_dir):
        os.makedirs(args.staging_dir)

    # Check if staging dir is empty
    if os.listdir(args.staging_dir):
        err = f"\nERROR: Staging directory is not empty: {args.staging_dir}"
        loggingC.message(err, threshold=-1)
        exit(1)



    return config