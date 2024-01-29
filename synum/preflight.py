import os

from datetime import datetime

from synum import loggingC, utility, enaSearching
from synum.statConf import staticConfig
from synum.webinWrapper import find_webin_cli_jar
from synum.binSubmission import query_ena_taxonomy

def __check_fields(items: list,
                   mandatory_fields: list,
                   category_name: str = "item"):
    """
    Check if the mandatory fields are present and not empty in each item of the
    given list.
    
    Args:
        items (list): The list of items to check.
        mandatory_fields (list): The list of fields that must be present in each
            item.
        category_name (str, optional): The name of the category being checked.
            Only used for error messages. Defaults to "item".
    """
    for item in items:
        for field in mandatory_fields:
            if not field in item.keys():
                err = f"\nERROR: At least one {category_name} entry is missing the '{field}' field."
                loggingC.message(err, threshold=-1)
                exit(1)
            if item[field] is None or item[field] == '':
                err = f"\nERROR: At least one {category_name} entry has an empty '{field}' field."
                loggingC.message(err, threshold=-1)
                exit(1)



def __check_date(date: str):
    """
    Check if the input is an ISO compliant date string.

    Args:
        date:    The date string to check.
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
        err = f"\nERROR: The date '{date}' is not a valid ISO date string. Please check your config file."
        loggingC.message(err, threshold=-1)
        exit(1)


def __check_country_sea_location(location: str):
    """
    Check if the input is a valid country or sea name.

    Args:
        location:    The location string to check.
    """
    valid_locations = staticConfig.valid_locations.split(';')
    if not location in valid_locations:
        err = f"\nERROR: The location '{location}' is not a valid country or sea name. Please check your config file."
        loggingC.message(err, threshold=-1)
        exit(1)

# def __check_config(args: argparse.Namespace,
#                    config: dict) -> None:
#     """
#     Does a superficial check of the config file.

#     Args:
#         args:    The command line arguments.
#         config:  The config file as a dictionary.
#     """
#     return # THIS NEEDS TO BE REWORKED
#     loggingC.message(f">Checking config file at {args.config}", threshold=1)

#     # Check if everything in the bins directory looks like a fasta file
#     if args.submit_bins:
#         bins_directory = utility.from_config(config, 'BINS', 'BINS_DIRECTORY')
#         bin_files = os.listdir(bins_directory)
#         for bin_file in bin_files:
#             extension = '.' + bin_file.split('.')[-1]
#             if not extension in staticConfig.fasta_extensions.split(';'):
#                 loggingC.message(f"WARNING: File {bin_file} in the bins directory does not end in {staticConfig.fasta_extensions} and will be skipped.", threshold=-1)
#     if args.submit_assembly:
#         # Check if assembly fasta file looks correct
#         fasta_path = utility.from_config(config, 'ASSEMBLY', 'FASTA_FILE')
#         utility.check_fasta(fasta_path)
#         ## Is the molecule type valid?
#         #molecule_type = utility.from_config(config, 'ASSEMBLY', 'MOLECULE_TYPE')
#         #if not molecule_type in staticConfig.molecule_types:
#         #    print(f"\nERROR: Molecule type '{molecule_type}' is not valid. Valid molecule types are: {', '.join(staticConfig.molecule_types)}")
#         #    exit(1)
#         #if not molecule_type.startswith('genomic'):
#         #loggingC.message(f"WARNING: Molecule type is set to '{molecule_type}' - is this a mistake?", threshold=0)

        
#         ## Is the assembly date valid?
#         #__check_date(utility.from_config(config, 'ASSEMBLY', 'DATE'))

#     # Check if the assembly taxid is valid and matches the scientific name
#     if args.submit_assembly:
#         loggingC.message(f">Checking if assembly taxid is valid", threshold=1)
#         assembly_taxid = utility.from_config(config, 'ASSEMBLY', 'TAXID')
#         assembly_scientific_name = utility.from_config(config, 'ASSEMBLY', 'SPECIES_SCIENTIFIC_NAME')

#         taxdata = query_ena_taxonomy(level="metagenome",
#                                     domain="metagenome",
#                                     classification=assembly_scientific_name,
#                                     filtered=True)
#         if len(taxdata) == 0 or len(taxdata) > 1:
#             err = f"\nERROR: The scientific name '{assembly_scientific_name}' is not valid."
#             loggingC.message(err, threshold=-1)
#             exit(1)
#         taxdata = taxdata[0]
#         if not taxdata['tax_id'] == assembly_taxid:
#             err = f"\nERROR: The taxid '{assembly_taxid}' does not match the scientific name '{assembly_scientific_name}'."
#             loggingC.message(err, threshold=-1)
#             exit(1)
        
#     # Check if the BAM files exist and are indexed/sorted
#     for bam_file in utility.from_config(config, 'BAM_FILES'):
#         if not os.path.isfile(bam_file):
#             err = f"\nERROR: BAM file {bam_file} does not exist."
#             loggingC.message(err, threshold=-1)
#             exit(1)
#         extension = '.' + bam_file.split('.')[-1]
#         if not extension in staticConfig.bam_extensions.split(';'):
#             err = f"\nERROR: BAM file {bam_file} has an invalid extension {extension}. Valid extensions are {staticConfig.bam_extensions}."
#             loggingC.message(err, threshold=-1)
#             exit(1)

#     # Query ENA to check if the various accessions (assembly, run_refs,
#     # sample_refs) are valid
#     # TODO

#     # Test if the taxonomy files exist and look like taxonomy files.
#     # TODO

#     # Do the taxonomy files cover every bin in the bins directory?
#     # TODO
            
#     # Are the read files gzipped fastq?
#     # TODO
            
#     # If --submit_reads, is all the required data present?
#     # TODO
#     # And are the fields with controlled vocabularies valid?
#     # TODO
#     # The different read sets must have unique names
#     # TODO
            
#     # If --submit_samples, is all the required data present?
#     # TODO

#     # If are not submitting an assembly, can we query the neccessary data?
            
#     # Passen die Assembly accessions? siehe diese message
#     print("""\nSince you chose not to submit an assembly, we assume that it is
#           already present in the ENA database. If this previously submitted
#           assembly is a co-assembly, fill out the field
#           \tEXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION
#           in the config file. If the assembly is based on a single sample,
#           fill out the field
#           \tEXISTING_ASSEMBLY_ANALYSIS_ACCESSION
#           in the config file.
#           Only fill out one of these fields an leave the other empty.""")
            
#     # The logging dir CANNOT be the same as the staging dir
#     if args.logging_dir == args.staging_dir:
#         err = f"\nERROR: The logging directory cannot be the same as the staging directory."
#         loggingC.message(err, threshold=-1)
#         exit(1)



def __check_study(config: dict,
                  testmode: bool) -> None:
    study_accession = utility.from_config(config, 'STUDY')
    if not enaSearching.study_exists(study_accession, testmode):
        if testmode:
            err = f"\nERROR: The study accession '{study_accession}' does not exist on the ENA development server which you are trying to submit to. If you created it on the regular server, it can take up to 24 hours until it shows up on the development server."
        else:
            err = f"\nERROR: The study accession '{study_accession}' does not exist on the ENA production server which you are trying to submit to. Did you create it on the development server?"
        loggingC.message(err, threshold=-1)
        exit(1)


def __check_samples(arguments: dict,
                    config: dict):
    """
    """
    if arguments['submit_samples']:
        # Check data in SAMPLES section
        sample_items = utility.from_config(config, 'SAMPLES')
        if len(sample_items) == 0:
            err = f"\nERROR: You chose to submit samples, but did not provide any sample data."
            loggingC.message(err, threshold=-1)
            exit(1)
        mandatory_fields = ['collection_date', 'geographic location (country and/or sea)']
        __check_fields(sample_items, mandatory_fields, category_name="sample")
        for s in sample_items:
            __check_date(s['collection_date'])
            __check_country_sea_location(s['geographic location (country and/or sea)'])


def __check_reads(paired: bool,
                  read_items: list,
                  arguments: dict,
                  testmode: bool):
    """
    """
    if paired:
        read_type = 'paired-end reads'
    else:
        read_type = 'single reads'
    if len(read_items) == 0:
        err = f"\nERROR: You chose to submit {type}, but did not provide any data in the config."
        loggingC.message(err, threshold=-1)
        exit(1)
    mandatory_fields = ['NAME',
                        'LIBRARY_SOURCE',
                        'LIBRARY_SELECTION',
                        'LIBRARY_STRATEGY']
    if paired:
        mandatory_fields.extend(['FASTQ1_FILE',
                                 'FASTQ2_FILE'])
    else:
        mandatory_fields.append('FASTQ_FILE')
    if arguments['submit_samples']:
        mandatory_fields.append('RELATED_SAMPLE_TITLE')
    else:
        mandatory_fields.append('RELATED_SAMPLE_ACCESSION')
    for s in read_items:
        # Check if all fields are present and not empty
        __check_fields(read_items,
                       mandatory_fields,
                       category_name=read_type)
        # Check if the sample accession exists
        if not arguments['submit_samples']:
            sample_accession = s['RELATED_SAMPLE_ACCESSION']
            if not enaSearching.sample_exists(sample_accession, testmode):
                err = f"\nERROR: The sample accession '{sample_accession}' does not exist on the ENA server."
                loggingC.message(err, threshold=-1)
                exit(1)
        # Check if the FASTQ file exists and has a valid file extension
        fastq_filepath = s['FASTQ_FILE']
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


def __check_single_reads(arguments: dict,
                         config: dict,
                         testmode: bool):
    if arguments['submit_single_reads']:
        read_items = utility.from_config(config, 'SINGLE_READS')
        __check_reads(paired=True,
                      read_items=read_items,
                      arguments=arguments,
                      testmode=testmode)

    
def __check_paired_reads(arguments: dict,
                         config: dict,
                         testmode: bool):
    if arguments['submit_paired_reads']:
        read_items = utility.from_config(config, 'PAIRED_END_READS')
        __check_reads(paired=True,
                      read_items=read_items,
                      arguments=arguments,
                      testmode=testmode)


def __check_misc(arguments: dict,
                 config: dict):
    """
    """
    # Platform
    if arguments['submit_assembly'] or arguments['submit_bins'] or arguments['submit_mags']:
        platform = utility.from_config(config, 'PLATFORM')
        if not platform in staticConfig.valid_platforms:
            err = f"\nERROR: The platform '{platform}' is not valid. Valid platforms are: {'|'.join(staticConfig.platforms)}"
            loggingC.message(err, threshold=-1)
            exit(1)

    # Project Name
    if arguments['submit_mags']:
        utility.from_config(config, 'PROJECT_NAME')

    # Metagenome taxonomy
    if arguments['submit_assembly']:
        metagenome_scientific_name = utility.from_config(config, 'METAGENOME_SCIENTIFIC_NAME')
        metagenome_taxid = utility.from_config(config, 'METAGENOME_TAXID')
        taxdata = query_ena_taxonomy(level="metagenome",
                                     domain="metagenome",
                                     classification=metagenome_scientific_name,
                                     filtered=True)
        if len(taxdata) == 0 or len(taxdata) > 1:
            err = f"\nERROR: The scientific name '{metagenome_scientific_name}' is not valid."
            loggingC.message(err, threshold=-1)
            exit(1)
        taxdata = taxdata[0]
        if not taxdata['tax_id'] == metagenome_taxid:
            err = f"\nERROR: The taxid '{metagenome_taxid}' does not match the scientific name '{metagenome_scientific_name}'."
            loggingC.message(err, threshold=-1)
            exit(1)


def __check_assembly(arguments: dict,
                     config: dict,
                     testmode: bool):
    """
    """
    if testmode:
        servertype = "development"
    else:
        servertype = "production"
    if not arguments['submit_assembly']:
        if 'EXISTING_ASSEMBLY_ANAYLSIS_ACCESSION' in config.keys():
            assembly_analysis_accession = utility.from_config(config,
                                                              'ASSEMBLY',
                                                              'EXISTING_ASSEMBLY_ANAYLSIS_ACCESSION')
            sample_accessions = enaSearching.search_samples_by_assembly_analysis(assembly_analysis_accession, testmode)
        elif 'EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION' in config.keys():
            sample_accessions = utility.from_config(config, 'ASSEMBLY', 'EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION')
            if not enaSearching.sample_exists(sample_accessions, testmode):
                err = f"\nERROR: The co-assembly sample accession '{sample_accessions}' could not be found on the {servertype} ENA server."
                loggingC.message(err, threshold=-1)
                exit(1)
        else:
            err = f"\nERROR: You chose not to submit an assembly, but did not provide an assembly accession."
            loggingC.message(err, threshold=-1)
            exit(1)


def __check_bins(arguments: dict,
                 config: dict,
                 testmode: bool):
    """
    """
    pass


def __check_mags(arguments: dict,
                 config: dict,
                 testmode: bool):
    """
    """
    pass


def __check_coverage(arguments: dict,
                     config: dict,
                     testmode: bool):
    """
    """
    pass


def preflight_checks(arguments: dict) -> None:
    """
    Check if everything looks like we can start.

    Args:
        args:    The command line arguments.

    Returns:
        The config file as a dictionary.
    """
    # Check if config file exists
    if not os.path.isfile(arguments['config']):
        err = f"\nERROR: The config file '{arguments['config']}' does not exist."
        loggingC.message(err, threshold=-1)
        exit(1)
    
    # Read data from the YAML config file
    config = utility.read_yaml(arguments['config'])

    # Check if the config file was filled out correctly
    testmode = arguments['devtest']
    __check_study(config, testmode)
    __check_misc(arguments, config)
    __check_samples(arguments, config)
    __check_single_reads(arguments, config, testmode)
    __check_paired_reads(arguments, config, testmode)
    __check_assembly(arguments, config, testmode)
    __check_bins(arguments, config, testmode)
    __check_mags(arguments, config, testmode)
    __check_coverage(arguments, config, testmode)

    # Check if webin-cli can be found
    loggingC.message(f">Checking if webin-cli can be found", threshold=1)
    find_webin_cli_jar()

    # Check for login data
    utility.get_login()

    # Create staging dir if it doesn't exist
    if not os.path.exists(arguments['staging_dir']):
        os.makedirs(arguments['staging_dir'])

    # Check if staging dir is empty
    if os.listdir(arguments['staging_dir']):
        err = f"\nERROR: Staging directory is not empty: {arguments['staging_dir']}"
        loggingC.message(err, threshold=-1)
        exit(1)

    return config