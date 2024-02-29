import os

from datetime import datetime

from synum import loggingC, utility, enaSearching
from synum.statConf import staticConfig
from synum.webinWrapper import find_webin_cli_jar
from synum.taxQuery import ena_taxonomy_suggestion
import time
import csv

def __check_tsv(tsvfile: str,
                required_columns: list):
    """
    Check if a .tsv file exists and has the required columns. If one of the 
    columns is "Bin_ids", return a list of all bin ids.

    Args:
        tsvfile:            The .tsv file to check.
        required_columns:   A list of column names that must be present in the
                            .tsv file.
    """
    if not os.path.isfile(tsvfile):
        err = f"\nERROR: The .tsv file '{tsvfile}' does not exist."
        loggingC.message(err, threshold=-1)
        exit(1)
    with open(tsvfile, 'r') as f:
        header = f.readline().strip().split('\t')
    for col in required_columns:
        if not col in header:
            err = f"\nERROR: The .tsv file '{tsvfile}' is missing the column '{col}'."
            loggingC.message(err, threshold=-1)
            exit(1)
    if 'Bin_ids' in header:
        bin_ids = []
        with open(tsvfile, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                bin_ids.append(row['Bin_ids'])
        return bin_ids
    

def __check_fields(items: list,
                   mandatory_fields: list,
                   optional: bool = False,
                   category_name: str = "item"):
    """
    Check if the mandatory fields are present and not empty in each item of the
    given list.
    
    Args:
        items (list): The list of items to check.
        mandatory_fields (list): List of tuples containing the name of a field
            and the type it should be. Each field must be present in each item
            of the list.
        optional (bool, optional): Whether or not the fields are optional. If
            True, the function will only checks if existing fields are of the
            correct type. Defaults to False.
        category_name (str, optional): The name of the category being checked.
            Only used for error messages. Defaults to "item".
    """
    if not isinstance(items, list):
        items = [items]
    for item in items:
        for field, field_type in mandatory_fields:
            if not field in item.keys():
                if not optional:
                    err = f"\nERROR: A '{field}' field is missing in the {category_name} section (or one of the items in this section)."
                    loggingC.message(err, threshold=-1)
                    exit(1)
            elif item[field] is None or item[field] == '':
                if not optional:
                    err = f"\nERROR: A '{field}' field is empty in the {category_name} section (or one of the items in this section)."
                    loggingC.message(err, threshold=-1)
                    exit(1)
            elif not isinstance(item[field], field_type):
                found_type = type(item[field]).__name__
                desired_type = field_type.__name__
                err = f"\nERROR: The '{field}' field in the {category_name} section (or one of the items in this section) is not of the correct type (type is <{found_type}> but should be <{desired_type}>)."
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


def __check_study(config: dict,
                  testmode: bool):
    """
    Check if the config contains a valid ENA study accession.

    Args:
        config:    The config file as a dictionary.
        testmode:  Whether or not to use the ENA development server.
    """
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
    Check if the SAMPLES section of the config file is valid.

    Args:
        arguments:    The command line arguments.
        config:       The config file as a dictionary.
    """
    if not arguments['submit_samples']:
        return
    # Check data in SAMPLES section
    sample_items = utility.from_config(config, 'NEW_SAMPLES')
    if len(sample_items) == 0:
        err = f"\nERROR: You chose to submit samples, but did not provide any sample data."
        loggingC.message(err, threshold=-1)
        exit(1)
    mandatory_fields = [('collection date', str),
                        ('geographic location (country and/or sea)', str)]
    __check_fields(sample_items, mandatory_fields, category_name="NEW_SAMPLE")
    for s in sample_items:
        __check_date(s['collection date'])
        __check_country_sea_location(s['geographic location (country and/or sea)'])


def __check_read_type(paired: bool,
                      read_items: list,
                      arguments: dict,
                      testmode: bool):
    """
    Check if a READS section is valid.

    Args:
        paired:       Whether or not the reads are paired-end.
        read_items:   The list of read entries to check.
        arguments:    The command line arguments.
        testmode:     Whether or not to use the ENA development server.
    """
    if paired:
        read_type = 'paired-end reads'
    else:
        read_type = 'single reads'
    if len(read_items) == 0:
        err = f"\nERROR: You chose to submit {type}, but did not provide any data in the config."
        loggingC.message(err, threshold=-1)
        exit(1)
    mandatory_fields = [('NAME', str),
                        ('LIBRARY_SOURCE', str),
                        ('LIBRARY_SELECTION', str),
                        ('LIBRARY_STRATEGY', str),]
    if paired:
        mandatory_fields.extend([('FASTQ1_FILE', str),
                                 ('FASTQ2_FILE', str),])
    else:
        mandatory_fields.append(('FASTQ_FILE',  str))
    if arguments['submit_samples']:
        mandatory_fields.append(('RELATED_SAMPLE_TITLE', str),)
    else:
        mandatory_fields.append(('RELATED_SAMPLE_ACCESSION',  str),)

    for s in read_items:
        # Check if all fields are present and not empty
        __check_fields(read_items,
                       mandatory_fields,
                       category_name=read_type)
        
        # Check if the sample accession exists
        if not arguments['submit_samples']:
            sample_accession = s['RELATED_SAMPLE_ACCESSION']
            if not enaSearching.sample_exists(sample_accession, testmode):
                err = f"\nERROR: The sample accession '{sample_accession}' was provided in the reads section but does not exist on the ENA server."
                loggingC.message(err, threshold=-1)
                exit(1)

        # Check if the FASTQ file exists and has a valid file extension
        if paired:
            fastq1_filepath = os.path.abspath(s['FASTQ1_FILE'])
            utility.check_fastq(fastq1_filepath)
            fastq2_filepath = os.path.abspath(s['FASTQ2_FILE'])
            utility.check_fastq(fastq2_filepath)
        else:
            fastq_filepath = os.path.abspath(s['FASTQ_FILE'])
            utility.check_fastq(fastq_filepath)


def __check_reads(arguments: dict,
                  config: dict,
                  testmode: bool):
    """
    """
    if not arguments['submit_reads']:
        return
    
    reads_present = False

    if 'SINGLE_READS' in config.keys():
        reads_present = True
        read_items = utility.from_config(config, 'SINGLE_READS')
        __check_read_type(paired=False,
                          read_items=read_items,
                          arguments=arguments,
                          testmode=testmode)
        
    if 'PAIRED_END_READS' in config.keys():
        reads_present = True
        read_items = utility.from_config(config, 'PAIRED_END_READS')
        __check_read_type(paired=True,
                          read_items=read_items,
                          arguments=arguments,
                          testmode=testmode)

    if not reads_present:
        err = f"\nERROR: You chose to submit reads, but did not provide any read data."
        loggingC.message(err, threshold=-1)
        exit(1)


def __check_misc(arguments: dict,
                 config: dict):
    """
    Check various fields of the config file not covered by other functions.

    Args:
        arguments:    The command line arguments.
        config:       The config file as a dictionary.
    """
    # Sequencing Platforms
    if arguments['submit_assembly'] or arguments['submit_bins'] or arguments['submit_mags']:
        sequencing_platforms = utility.from_config(config, 'SEQUENCING_PLATFORMS')
        if not isinstance(sequencing_platforms, list):
            sequencing_platforms = [sequencing_platforms]
        valid_platforms = staticConfig.valid_sequencing_platforms.split(';')
        for platform in sequencing_platforms:
            if not platform in valid_platforms:
                err = f"\nERROR: The sequencing platform '{platform}' is not valid. Valid platforms are: {'|'.join(staticConfig.valid_sequencing_platforms.split(';'))}"
                loggingC.message(err, threshold=-1)
                exit(1)

    # Project Name
    if arguments['submit_mags']:
        utility.from_config(config, 'PROJECT_NAME')

    # Metagenome taxonomy
    if arguments['submit_assembly']:
        metagenome_scientific_name = utility.from_config(config, 'METAGENOME_SCIENTIFIC_NAME')
        metagenome_taxid = utility.from_config(config, 'METAGENOME_TAXID')
        taxdata = ena_taxonomy_suggestion(level="metagenome",
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

def __check_assembly_name(assembly_name: str):
    """
    Check if the assembly name is too long. The submission limit is 50 characters,
    but webin cli will introduce add a prefix before submission.

    Args:
        assembly_name:    The assembly name read from the config.
    """
    max_length = staticConfig.max_assembly_name_length
    if len(assembly_name) > max_length:
        err = f"\nERROR: The assembly name '{assembly_name}' is too long. The maximum length is {max_length} characters."
        loggingC.message(err, threshold=-1)
        exit(1)

def __check_assembly(arguments: dict,
                     config: dict,
                     testmode: bool):
    """
    Check if the ASSEMBLY section of the config file is valid.

    Args:
        arguments:    The command line arguments.
        config:       The config file as a dictionary.
        testmode:     Whether or not to use the ENA development server.
    """
    if testmode:
        servertype = "development"
    else:
        servertype = "production"

    assembly_data = utility.from_config(config, 'ASSEMBLY')
    __check_assembly_name(assembly_data['ASSEMBLY_NAME'])

    if arguments['submit_assembly']:
        
        if len(assembly_data) == 0:
            err = f"\nERROR: You chose to submit an assembly, but did not provide any assembly data."
            loggingC.message(err, threshold=-1)
            exit(1)
        mandatory_fields = [
            ('ASSEMBLY_NAME', str),
            ('ASSEMBLY_SOFTWARE', str),
            ('ISOLATION_SOURCE', str),
            ('FASTA_FILE', str),
            ('collection date', str),
            ('geographic location (country and/or sea)', str),
        ]
        __check_fields(assembly_data, mandatory_fields, category_name="ASSEMBLY")
        __check_date(assembly_data['collection date'])
        __check_country_sea_location(assembly_data['geographic location (country and/or sea)'])
        if utility.is_fasta(assembly_data['FASTA_FILE']) is None:
            valid_extensions = staticConfig.fasta_extensions.split(';')
            gz_extensions = [f"{ext}.gz" for ext in valid_extensions]
            err = f"\nERROR: The assembly fasta file '{assembly_data['FASTA_FILE']}' does not exist or does not have a valid file extensions. Valid extensions are {'|'.join(valid_extensions)} and {'|'.join(gz_extensions)}." 
            loggingC.message(err, threshold=-1)
            exit(1)
        

    else:
        biological_sample_accessions = utility.from_config(config, 'SAMPLE_ACCESSIONS')
        if not isinstance(biological_sample_accessions, list):
            biological_sample_accessions = [biological_sample_accessions]
        resulting_accession = None
        if 'EXISTING_ASSEMBLY_ANALYSIS_ACCESSION' in assembly_data:
            assembly_analysis_accession = utility.optional_from_config(config,
                                                                       'ASSEMBLY',
                                                                       'EXISTING_ASSEMBLY_ANALYSIS_ACCESSION')
            if not assembly_analysis_accession is None or assembly_analysis_accession == '':
                resulting_accession = enaSearching.search_samples_by_assembly_analysis(assembly_analysis_accession, testmode)
                if not len(biological_sample_accessions) == 1:
                    err = f"\nERROR: When providing an existing assembly analysis accession, you need to provide exactly one biological sample accession in the SAMPLE_ACCESSIONS field. If the assembly stems from 2 or more samples, please provide a co-assembly accession instead."
                    loggingC.message(err, threshold=-1)
                    exit(1) 
            else:
                resulting_accession = None
        if resulting_accession is None and 'EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION' in assembly_data:
            sample_accessions = utility.optional_from_config(config, 'ASSEMBLY', 'EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION')
            if not sample_accessions is None or sample_accessions == '':
                if not enaSearching.sample_exists(sample_accessions, testmode):
                    err = f"\nERROR: The co-assembly sample accession '{sample_accessions}' could not be found on the {servertype} ENA server."
                    loggingC.message(err, threshold=-1)
                    exit(1)
                else:
                    resulting_accession = sample_accessions
                    if len(biological_sample_accessions) < 2:
                        err = f"\nERROR: When providing an existing co-assembly sample accession, you need to provide at least two biological sample accessions in the SAMPLE_ACCESSIONS field."
                        loggingC.message(err, threshold=-1)
                        exit(1)
            else:
                resulting_accession = None
        if (not 'EXISTING_ASSEMBLY_ANALYSIS_ACCESSION' in assembly_data) and (not 'EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION' in assembly_data):
            err = f"\nERROR: You chose not to submit an assembly, but did not provide an assembly accession."
            loggingC.message(err, threshold=-1)
            exit(1)
        if resulting_accession is None:
            err = f"\nPlease provide either an existing assembly analysis accession or an existing co-assembly sample accession."
            loggingC.message(err, threshold=-1)
            exit(1)


def __check_bins(arguments: dict,
                 config: dict,
                 testmode: bool):
    """
    Check if the BINS section of the config file is valid.

    Args:
        arguments:    The command line arguments.
        config:       The config file as a dictionary.
        testmode:     Whether or not to use the ENA development server.
    """
    if not arguments['submit_bins'] and not arguments['submit_mags']:
        return
    
    # Check if all fields are present and not empty
    bin_data = utility.from_config(config, 'BINS')
    if len(bin_data) == 0:
        err = f"\nERROR: You chose to submit bins, but did not provide any bin data."
        loggingC.message(err, threshold=-1)
        exit(1)
    mandatory_fields = [('BINS_DIRECTORY', str),
                        ('COMPLETENESS_SOFTWARE', str),
                        ('QUALITY_FILE', str),
                        ('BINNING_SOFTWARE', str),]
    __check_fields(bin_data, mandatory_fields, category_name="BINS")
    
    # Check quality file existence and columns
    quality_file = bin_data['QUALITY_FILE']
    if quality_file is None or quality_file == '':
        err = f"\nERROR: No QUALITY_FILE was provided in the BINS section."
        loggingC.message(err, threshold=-1)
        exit(1)
    __check_tsv(quality_file, staticConfig.bin_quality_columns.split(';'))


    # Check if at least one NCBI_TAXONOMY_FILE or MANUAL_TAXONOMY_FILE exists
    tax_files = []
    if 'NCBI_TAXONOMY_FILES' in bin_data.keys():
        ncbi_tax_files = bin_data['NCBI_TAXONOMY_FILES']
        if not isinstance(ncbi_tax_files, list):
            ncbi_tax_files = [ncbi_tax_files]
        tax_files.extend(ncbi_tax_files)
    # And if the headers of the NCBI_TAXONOMY_FILES are correct
    for tax_file in tax_files:
        if not os.path.isfile(tax_file):
            err = f"\nERROR: The taxonomy file '{tax_file}' does not exist."
            loggingC.message(err, threshold=-1)
            exit(1)
        gtdb_majority_vote_columns = staticConfig.gtdb_majority_vote_columns.split(';')
        ncbi_taxonomy_columns = staticConfig.ncbi_taxonomy_columns.split(';')
        with open(tax_file, 'r') as f:
            header = f.readline().strip().split('\t')
            if not header == gtdb_majority_vote_columns:
                for item in ncbi_taxonomy_columns:
                    if not item in header:
                        err = f"\nERROR: The taxonomy file '{tax_file}' needs to have one of the following two sets of columns:\n{'|'.join(gtdb_majority_vote_columns)}\n{'|'.join(ncbi_taxonomy_columns)}"
                        loggingC.message(err, threshold=-1)
                        exit(1)
    if 'MANUAL_TAXONOMY_FILE' in bin_data.keys():
        if isinstance(bin_data['MANUAL_TAXONOMY_FILE'], list):
            err = f"\nERROR: In the BINS section, provide only one MANUAL_TAXONOMY_FILE please"
            loggingC.message(err, threshold=-1)
            exit(1)
        if not bin_data['MANUAL_TAXONOMY_FILE'] is None:
            if bin_data['MANUAL_TAXONOMY_FILE'] == '':
                err = f"\nERROR: Ane empty string was provided as MANUAL_TAXONOMY_FILE in the BINS section."
                err += f"\nPlease provide a valid file path or remove the field from the config file."
                loggingC.message(err, threshold=-1)
                exit(1)
            __check_tsv(bin_data['MANUAL_TAXONOMY_FILE'], staticConfig.manual_taxonomy_columns.split(';'))
            tax_files.append(bin_data['MANUAL_TAXONOMY_FILE'])
    # And if the headers of the MANUAL_TAXONOMY_FILE are correct
            
    # Now check there actual are tax files
    if len(tax_files) == 0:
        err = f"\nERROR: You chose to submit bins, but did not provide any taxonomy files."
        loggingC.message(err, threshold=-1)
        exit(1)


    # Check if the bins directory exists and contains at least one bin
    bins_directory = bin_data['BINS_DIRECTORY']
    if not os.path.isdir(bins_directory):
        err = f"\nERROR: The bins directory '{bins_directory}' does not exist."
        loggingC.message(err, threshold=-1)
        exit(1)
    if len(os.listdir(bins_directory)) == 0:
        err = f"\nERROR: The bins directory '{bins_directory}' is empty."
        loggingC.message(err, threshold=-1)
        exit(1)
    found = False
    for file in os.listdir(bins_directory):
        if not (utility.is_fasta(os.path.join(bins_directory, file)) is None):
            found = True
            break
    if not found:
        err = f"\nERROR: The bins directory '{bins_directory}' does not contain any fasta files."
        loggingC.message(err, threshold=-1)
        exit(1)

    # Check if the required arguments in ASSEMBLY section are present
    assembly_data = utility.from_config(config, 'ASSEMBLY')
    mandatory_fields = [('ASSEMBLY_SOFTWARE', str),
                        ('collection date', str),
                        ('geographic location (country and/or sea)', str),]
    __check_fields(assembly_data, mandatory_fields, category_name="ASSEMBLY")
    __check_date(assembly_data['collection date'])
    __check_country_sea_location(assembly_data['geographic location (country and/or sea)'])


def __check_mags(arguments: dict,
                 config: dict,
                 testmode: bool):
    """
    Check if the MAGS section of the config file is valid.

    Args:
        arguments:    The command line arguments.
        config:       The config file as a dictionary.
        testmode:     Whether or not to use the ENA development server.
    """
    if not arguments['submit_mags']:
        return
    
    # Check project name
    utility.from_config(config, 'PROJECT_NAME')

    # Check the metadata file
    metadata_file = utility.from_config(config, 'MAGS', 'MAG_METADATA_FILE')
    if metadata_file is None or metadata_file == '':
        err = f"\nERROR: No MAG_METADATA_FILE was provided in the MAGS section."
        loggingC.message(err, threshold=-1)
        exit(1)
    __check_tsv(metadata_file, staticConfig.mag_metadata_columns.split(';'))

    # Check fields in ASSEMBLY section
    assembly_data = utility.from_config(config, 'ASSEMBLY')
    mandatory_fields = [('ASSEMBLY_SOFTWARE', str),
                        ('collection date', str),
                        ('geographic location (country and/or sea)', str),]
    __check_fields(assembly_data, mandatory_fields, category_name="ASSEMBLY")
    __check_date(assembly_data['collection date'])
    __check_country_sea_location(assembly_data['geographic location (country and/or sea)'])
    assembly_additional_data = utility.from_config(config, 'ASSEMBLY', 'ADDITIONAL_SAMPLESHEET_FIELDS')
    mandatory_fields = [
        ('broad-scale environmental context', str),
        ('local environmental context', str),
        ('environmental medium', str),
        ('geographic location (latitude)', str),
        ('geographic location (longitude)', str),
    ]
    __check_fields(assembly_additional_data, mandatory_fields, category_name="ASSEMBLY")

    # Check the BINS section (basic checks will already have been done in __check_bins)
    bins_additional_data = utility.from_config(config, 'BINS', 'ADDITIONAL_SAMPLESHEET_FIELDS')
    mandatory_fields = [
        ('binning parameters', str),
        ('taxonomic identity marker', str),
    ]
    __check_fields(bins_additional_data, mandatory_fields, category_name="BINS")


def __check_coverage(arguments: dict,
                     config: dict,
                     testmode: bool):
    """
    Check if there is valid coverage information provided in the config file.

    Args:
        arguments:    The command line arguments.
        config:       The config file as a dictionary.
        testmode:     Whether or not to use the ENA development server.
    """
    # Do we even need coverage values?
    if not arguments['submit_assembly'] and not arguments['submit_bins'] and not arguments['submit_mags']:
        return

    # Check if we have direct coverage values
    coverage_values = True

    # Are coverage values provided for the assembly?
    if arguments['submit_assembly']:
        assembly_data = utility.from_config(config, 'ASSEMBLY')
        if not 'COVERAGE_VALUE' in assembly_data.keys():
            coverage_values = False
        else:
            # Check if the coverage value string can be cast to float
            try:
                float(assembly_data['COVERAGE_VALUE'])
            except ValueError:
                err = f"\nERROR: The coverage value '{assembly_data['COVERAGE_VALUE']}' is not a float value."
                loggingC.message(err, threshold=-1)
                exit(1)

    # Are coverage values provided for the bins/MAGs?
    if arguments['submit_bins'] or arguments['submit_mags']:
        bin_data = utility.from_config(config, 'BINS')
        if not 'COVERAGE_FILE' in bin_data.keys():
            coverage_values = False
        else:
            # Check if the coverage file exists and has valid headers
            bin_coverage_file = bin_data['COVERAGE_FILE']
            if bin_coverage_file is None or bin_coverage_file == '':
                err = f"\nERROR: The field COVERAGE_FILE in the BINS section is empty."
                loggingC.message(err, threshold=-1)
                exit(1)
            __check_tsv(bin_coverage_file, staticConfig.bin_coverage_columns.split(';'))

    # Are there bam files?
    coverage_bams = False
    if 'BAM_FILES' in config.keys():
        bam_files = utility.from_config(config, 'BAM_FILES')
        if not isinstance(bam_files, list):
            bam_files = [bam_files]
        if len(bam_files) > 0:
            coverage_bams = True
            # Check if the BAM files exist and have valid extensions
            for bam_file in bam_files:
                if not os.path.isfile(bam_file):
                    err = f"\nERROR: The BAM file '{bam_file}' does not exist."
                    loggingC.message(err, threshold=-1)
                    exit(1)
                extension = '.' + bam_file.split('.')[-1]
                if not extension in staticConfig.bam_extensions.split(';'):
                    err = f"\nERROR: The BAM file '{bam_file}' has an invalid extension {extension}. Valid extensions are {staticConfig.bam_extensions}."
                    loggingC.message(err, threshold=-1)
                    exit(1)

    # Check if we have at least one coverage source
    if not coverage_values and not coverage_bams:
        err = f"\nERROR: You chose to submit an assembly, bins or MAGs. You need to provide either .BAM files or a known coverage (for assembly AND bins)."
        loggingC.message(err, threshold=-1)
        exit(1)
    if coverage_values and coverage_bams:
        err = f"You provided both a known coverage value and .BAM files. The .BAM files will be ignored."
        loggingC.message(err, threshold=0)



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

    # Skip checks if requested
    if arguments['skip_checks'] == True:
        message = f"WARNING: Skipping ALL preflight checks."
        delay = 3
        time.sleep(delay)
        loggingC.message(message, threshold=0)
        return config

    # Check if the config file was filled out correctly
    testmode = arguments['development_service']
    __check_study(config, testmode)
    __check_misc(arguments, config)
    __check_samples(arguments, config)
    __check_reads(arguments, config, testmode)
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

    msg = f">All preflight checks passed."
    loggingC.message(msg, threshold=0)

    return config
