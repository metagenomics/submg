import os
import yaml

def __write_config(config: dict,
                   outpath: str) -> None:
    """
    Write the config to file.

    Args:
        config (dict): The config dictionary
        outpath (str): The path where the config should be written
    """
  
    def represent_none(self, _):
        """
        We need this to write fields without values to the YAML file.
        """
        return self.represent_scalar('tag:yaml.org,2002:null', '')
    
    yaml.add_representer(type(None), represent_none)

    outpath = os.path.abspath(outpath)
    if os.path.exists(outpath):
        print(f"\nERROR: The file '{outpath}' already exists.")
        exit(1)

    with open(outpath, 'w') as outfile:
        yaml.dump(config, outfile, default_flow_style=False)

    print(f">Config with empty fields written to {outpath}")


def __check_parameters(outpath: str,
                submit_samples: int,
                submit_single_reads: int,
                submit_paired_end_reads: int,
                coverage_from_bam: bool,
                known_coverage: bool,
                submit_assembly: bool,
                submit_bins: bool,
                submit_mags: bool) -> None:
    """
    Check if the parameters in their combination are valid. If not, fail
    gracefully.

    Args:
        outpath (str): The path where the config should be written
        submit_samples (int): The number of samples to be submitted
        submit_single_reads (int): The number of single read sets to be submitted
        submit_paired_end_reads (int): The number of paired-end read sets to be submitted
        coverage_from_bam (bool): Whether the coverage should be calculated from a BAM file
        known_coverage (bool): Whether the coverage is already known
        submit_assembly (bool): Whether an assembly should be submitted
        submit_bins (bool): Whether bins should be submitted
        submit_mags (bool): Whether MAGs should be submitted
    """
    # Check if the output directory exists
    output_directory = os.path.dirname(outpath) or '.'  # Use current directory if no directory in outpath
    if not os.path.exists(output_directory):
        print(f"\nERROR: The directory '{output_directory}' where '{outpath}' should be written does not exist.")
        exit(1)

    # The valid submission modes we support are 
    submission_modes = """The following modes of submission are supported:
	# Samples > Reads > Assembly > Bins > MAGs
    # Samples > Reads > Assembly > Bins
    # Samples > Reads > Assembly
    # Reads > Assembly > Bins > MAGs
    # Reads > Assembly > Bins
    # Reads > Assembly
    # Assembly > Bins > MAGs
    # Assembly > Bins
    # Assembly
    # Bins > MAGs
    # Bins
    # MAGs
    # Submitting single and paired reads at the same time works.
    """

    # Do we lack coverage data or have redundancy
    if (coverage_from_bam + known_coverage) != 1:
        print(f"\nERROR: You must specify exactly one of --coverage-from-bam or --known-coverage.")
        exit(1)

    # Are we submitting any reads?
    if submit_single_reads or submit_paired_end_reads:
        submit_reads = True
    else:
        submit_reads = False

    # Check if the user has specified a valid mode
    is_valid = False
    if ((submit_mags and not submit_bins) and (submit_samples or submit_reads or submit_assembly)): # MAGs can only be submitted with bins or alone
        is_valid = False
    elif (submit_samples and submit_reads and submit_assembly): # Mode 1-3
        is_valid = True
    elif (submit_reads and submit_assembly and not submit_samples): # Mode 4-6
        is_valid = True
    if (submit_assembly and submit_bins and not submit_samples and not submit_reads): # Mode 7-9
        is_valid = True
    if (submit_bins and submit_mags and not submit_assembly and not submit_samples and not submit_reads): # Mode 10
        is_valid = True
    if ((submit_bins or submit_mags) and not submit_assembly and not submit_samples and not submit_reads): # Mode 11
        is_valid = True

    if not is_valid:
        print(f"\nERROR: The combination of parameters you have specified is not valid.")
        print(submission_modes)
        exit(1)


def __make_config_dict(submit_samples: int,
                       submit_single_reads: int,
                       submit_paired_end_reads: int,
                       coverage_from_bam: bool,
                       known_coverage: bool,
                       submit_assembly: bool,
                       submit_bins: bool,
                       submit_mags: bool) -> None:
    """
    Create the config dictionary.

    Args:
        submit_samples (int): The number of samples to be submitted
        submit_single_reads (int): The number of single read sets to be submitted
        submit_paired_end_reads (int): The number of paired-end read sets to be submitted
        coverage_from_bam (bool): Whether the coverage should be calculated from a BAM file
        known_coverage (bool): Whether the coverage is already known
        submit_assembly (bool): Whether an assembly should be submitted
        submit_bins (bool): Whether bins should be submitted
        submit_mags (bool): Whether MAGs should be submitted

    Returns:
        dict: The config dictionary
    """

    # Create the config dictionary. We always need a 'STUDY' field
    config = {'STUDY': ""}

    # Metagenome taxonomy
    # We need the scientific & taxid name for everything except reads
    # If the assembly was already submitted, we can derive the taxonomy from the assembly
    if submit_assembly:
        config['METAGENOME_SCIENTIFIC_NAME'] = ""
        config['METAGENOME_TAXID'] = ""

    # Platform - needed for assembly and bins
    if submit_assembly or submit_bins or submit_mags:
        config['SEQUENCING_PLATFORMS'] = [""]

    # Make the SAMPLE section
    samples = []
    for _ in range(submit_samples):
        entry = {'TITLE': "",
                 'collection date': "",
                 'geographic location (country and/or sea)': "",
                 'ADDITIONAL_SAMPLESHEET_FIELDS': None}
        if submit_mags: # MAGs require location, so we might as well ask for them here
            entry['ADDITIONAL_SAMPLESHEET_FIELDS']['geographic location (latitude)'] = ""
            entry['ADDITIONAL_SAMPLESHEET_FIELDS']['geographic location (longitude)'] = ""
            entry['ADDITIONAL_SAMPLESHEET_FIELDS']['broad-scale environmental context'] = ""
            entry['ADDITIONAL_SAMPLESHEET_FIELDS']['local environmental context'] = ""
            entry['ADDITIONAL_SAMPLESHEET_FIELDS']['environmental medium'] = ""
        samples.append(entry)
    if len(samples) > 0:
        config['NEW_SAMPLES'] = samples
    else:
        config['SAMPLE_ACCESSIONS'] = [""]

    # Make the SINGLE READ section
    reads = []
    for _ in range(submit_single_reads):
        entry = {'NAME': "",
                 'SEQUENCING_INSTRUMENT': "",
                 'LIBRARY_SOURCE': "",
                 'LIBRARY_SELECTION': "",
                 'LIBRARY_STRATEGY': "",
                 'FASTQ_FILE': ""}
        if submit_samples > 0:
            entry['RELATED_SAMPLE_TITLE'] = ""
        else:
            entry['RELATED_SAMPLE_ACCESSION'] = ""
        reads['ADDITIONAL_MANIFEST_FIELDS'] = None
        reads.append(entry)
    if len(reads) > 0:
        config['SINGLE_READS'] = reads

    # Make the PAIRED-END READ section
    reads = []
    for _ in range(submit_paired_end_reads):
        entry = {'NAME': "",
                 'SEQUENCING_INSTRUMENT': "",
                 'LIBRARY_SOURCE': "",
                 'LIBRARY_SELECTION': "",
                 'LIBRARY_STRATEGY': "",
                 'INSERT_SIZE': "",
                 'FASTQ1_FILE': "",
                 'FASTQ2_FILE': ""}
        if submit_samples > 0:
            entry['RELATED_SAMPLE_TITLE'] = ""
        else:
            entry['RELATED_SAMPLE_ACCESSION'] = ""
        entry['ADDITIONAL_MANIFEST_FIELDS'] = None
        reads.append(entry)
    if len(reads) > 0:
        config['PAIRED_END_READS'] = reads

    # Make the ASSEMBLY section
    assembly = {
        'ASSEMBLY_NAME': "",
    }
    if not submit_assembly:
        assembly['ASSEMBLY_ACCESSION'] = ""
    else:
        assembly['ASSEMBLY_SOFTWARE'] = ""
        assembly['ISOLATION_SOURCE'] = ""
        assembly['geographic location (country and/or sea)'] = ""
        assembly['collection_date'] = ""
        assembly['FASTA_FILE'] = ""
        assembly['ADDITIONAL_SAMPLESHEET_FIELDS'] = None
        assembly['ADDITIONAL_MANIFEST_FIELDS'] = None
    if (submit_single_reads + submit_paired_end_reads) == 0: # We need the accessions of the reads
        assembly['RUN_ACCESSIONS'] = [""]
    if submit_mags: # Since we need this for MAGs, we might as well ask for it here
        assembly['ADDITIONAL_SAMPLESHEET_FIELDS'] = {
            'broad-scale environmental context': "",
            'local environmental context': "",
            'environmental medium': "",
            'geographic location (latitude)': "",
            'geographic location (longitude)': "",
        }
    config['ASSEMBLY'] = assembly

    # Make the BINS section
    if submit_bins or submit_mags:
        bins = {
            'BINS_DIRECTORY': "",
            'COMPLETENESS_SOFTWARE': "",
            'BIN_QUALITY_FILE': "",
            'BIN_NCBI_TAXONOMY_FILES': [""],
            'MANUAL_TAXONOMY_FILE': "",
            'BINNING_SOFTWARE': "",
            'ADDITIONAL_SAMPLESHEET_FIELDS': None,
            'ADDITIONAL_MANIFEST_FIELDS': None
        }
        if submit_mags: # Since we need this for MAGs, we might as well ask for it here
            bins['ADDITIONAL_SAMPLESHEET_FIELDS'] = {
                'binning parameters': "",
                'taxonomic identity marker': "",
            }
        config['BINS'] = bins

    # Make the MAGs section (and add fields to the BINS section)
    if submit_mags:
        mags = {
            'MAG_NAMES_FILE': "",
            'MAG_QUALITY_FILE': "",
            'MAG_NCBI_TAXONOMY_FILES': [""],
            'MANUAL_TAXONOMY_FILE': "",
            'MAGS_SOFTWARE': "",
            'ADDITIONAL_SAMPLESHEET_FIELDS': None,
            'ADDITIONAL_MANIFEST_FIELDS': None
        }
        bins['MAGS'] = mags

    # Add coverage entries or bam file entries
    if submit_assembly or submit_bins or submit_mags:
        if coverage_from_bam:
            assert known_coverage == False
            config['BAM_FILES'] = [""]
        elif known_coverage:
            assert coverage_from_bam == False
            if submit_assembly:
                config['ASSEMBLY']['COVERAGE_VALUE'] = ""
            if submit_bins:
                config['BINS']['COVERAGES_FILE'] = ""
        else:
            raise ValueError("Either coverage_from_bam or known_coverage must be set to True")
        
    return config

def make_config(outpath: str,
                submit_samples: int,
                submit_single_reads: int,
                submit_paired_end_reads: int,
                coverage_from_bam: bool,
                known_coverage: bool,
                submit_assembly: bool,
                submit_bins: bool,
                submit_mags: bool) -> None:
    """
    Write an empty YAML config file which holds the keys (but not the values)
    which the user needs.

    Args:
        outpath (str): The path where the config should be written
        submit_samples (int): The number of samples to be submitted
        submit_single_reads (int): The number of single read sets to be submitted
        submit_paired_end_reads (int): The number of paired-end read sets to be submitted
        coverage_from_bam (bool): Whether the coverage should be calculated from a BAM file
        known_coverage (bool): Whether the coverage is already known
        submit_assembly (bool): Whether an assembly should be submitted
        submit_bins (bool): Whether bins should be submitted
        submit_mags (bool): Whether MAGs should be submitted
    """
    __check_parameters(outpath,
                       submit_samples,
                       submit_single_reads,
                       submit_paired_end_reads,
                       coverage_from_bam,
                       known_coverage,
                       submit_assembly,
                       submit_bins,
                       submit_mags)

    
    # Assemble all the fields we need
    config_fields = __make_config_dict(submit_samples,
                                       submit_single_reads,
                                       submit_paired_end_reads,
                                       coverage_from_bam,
                                       known_coverage,
                                       submit_assembly,
                                       submit_bins,
                                       submit_mags)
    
    # Write to file
    __write_config(config_fields,
                   outpath)
    
#make_config("/mnt/mega/testing_colpymag/config/test.yaml", 2, 4, True, False)



    
# def __LEOLD_make_config_dict(submit_samples: int,
#                        submit_single_reads: int,
#                        submit_paired_end_reads: int,
#                        coverage_from_bam: bool,
#                        known_coverage: bool,
#                        submit_assembly: bool,
#                        submit_bins: bool,
#                        submit_mags: bool) -> None:
#     """

#     """

#     # Create the config dictionary. We always need a 'STUDY' field
#     config = {'STUDY': ""}
    
#     # Metagenome taxonomy
#     # We need the scientific name for everything except reads
#     # If the assembly was already submitted, then we can derive the taxonomy
#     if not submit_assembly and submit_bins or submit_mags:
#         pass # We can derive the taxonomy from the assembly
#     elif submit_assembly or submit_bins or submit_mags or submit_samples:

#     elif not submit_assembly and 
#     if submit_samples > 0 or submit_assembly or submit_bins or submit_mags:
#         config['METAGENOME_SCIENTIFIC_NAME'] = ""
#     # we only need the taxid if we are submitting bins or an assembly
#     if (submit_samples > 0) or (submit_assembly > 0):
#         config['METAGENOME_TAXID'] = ""

#     # Platform - needed for assembly and bins
#     if submit_assembly or submit_bins or submit_mags:
#         config['SEQUENCING_PLATFORMS'] = [""]

#     # Make the SAMPLE section
#     samples = []
#     for _ in range(submit_samples):
#         entry = {'TITLE': "",
#                  'DESCRIPTION': "",
#                  'COLLECTION_DATE': "",
#                  'LOCATION': "",
#                  'OPTIONAL_FIELDS': None}
#         if submit_mags:
#             entry['OPTIONAL_FIELDS']['geographic location (latitude)'] = ""
#             entry['OPTIONAL_FIELDS']['geographic location (longitude)'] = ""
#         samples.append(entry)
#     if len(samples) > 0:
#         config['NEW_SAMPLES'] = samples
#     else:
#         if submit_assembly or submit_bins or submit_mags:
#             config['SAMPLE_ACCESSIONS'] = [""]

#     # Make the SINGLE READ section
#     reads = []
#     for _ in range(submit_single_reads):
#         entry = {'NAME': "",
#                  'READ_TYPE': "",
#                  'SEQUENCING_INSTRUMENT': "",
#                  'LIBRARY_SOURCE': "",
#                  'LIBRARY_SELECTION': "",
#                  'LIBRARY_STRATEGY': "",
#                  'FASTQ_FILE': "",
#                  'OPTIONAL_FIELDS': None}
#         if submit_samples > 0:
#             entry['RELATED_SAMPLE_TITLE'] = ""
#         else:
#             entry['RELATED_SAMPLE_ACCESSION'] = ""
#         reads.append(entry)
#     if len(reads) > 0:
#         config['SINGLE_READS'] = reads

#     # Make the PAIRED-END READ section
#     reads = []
#     for _ in range(submit_paired_end_reads):
#         entry = {'NAME': "",
#                  'READ_TYPE': "",
#                  'INSTRUMENT': "",
#                  'LIBRARY_SOURCE': "",
#                  'LIBRARY_SELECTION': "",
#                  'LIBRARY_STRATEGY': "",
#                  'FASTQ1_FILE': "",
#                  'FASTQ2_FILE': "",
#                  'OPTIONAL_FIELDS': None}
#         if submit_samples > 0:
#             entry['RELATED_SAMPLE_TITLE'] = ""
#         else:
#             entry['RELATED_SAMPLE_ACCESSION'] = ""
#         reads.append(entry)
#     if len(reads) > 0:
#         config['PAIRED_END_READS'] = reads

#     # Make the ASSEMBLY section
#     assembly = {}
#     if (not submit_assembly) and submit_bins or submit_mags:
#         assembly['ASSEMBLY_ACCESSION'] = ""
#     if submit_assembly or submit_bins or submit_mags:
#         assembly['ASSEMBLY_NAME'] = ""
#     if submit_assembly:
#         assembly['ASSEMBLY_SOFTWARE'] = ""
#         assembly['ISOLATION_SOURCE'] = ""
#         assembly['LOCATION'] = ""
#         assembly['FASTA_FILE'] = ""
#     if (not submit_single_reads) and (not submit_paired_end_reads):
#         assembly['READ_ACCESSIONS'] = [""]
#     if submit_assembly or submit_bins or submit_mags:
#         assembly['OPTIONAL_FIELDS'] = None

#     # Make the BINS section
#     if submit_bins or submit_mags:
#         bins = {
#             'BINS_DIRECTORY': "",
#             'COMPLETENESS_SOFTWARE': "",
#             'BIN_QUALITY_FILE': "",
#             'BIN_NCBI_TAXONOMY_FILES': [""],
#             'MANUAL_TAXONOMY_FILE': "",
#             'BINNING_SOFTWARE': "",
#         }

#     # Make the MAGs section (and add fields to the BINS section)
#     if submit_mags:
#         # Extra that can easily be provided on assembly level
#         assembly['broad-scale environmental context'] = ""
#         assembly['local environmental context'] = ""
#         assembly['environmental medium'] = ""
#         assembly['geographic location (latitude)'] = ""
#         assembly['geographic location (longitude)'] = ""
#         # Extra information needed on bin level
#         bins['BINNING_PARAMETERS'] = ""
#         bins['TAXONOMIC_IDENTITY_MARKER'] = ""
#         mags = {
#             'MAG_NAMES_FILE': "",
#         }

            
#         mags = {
#             'MAGS_FILE': "",
#             'MAG_QUALITY_FILE': "",
#             'MAG_NCBI_TAXONOMY_FILES': [""],
#             'MANUAL_TAXONOMY_FILE': "",
#             'MAGS_SOFTWARE': "",
#         }
#         bins['MAGS'] = mags

#     # Add optional fields to assembly, bins, mags
#     if submit_assembly:
#         assembly['OPTIONAL_FIELDS'] = None
#     if submit_bins or submit_mags:
#         bins['OPTIONAL_FIELDS'] = None
#     if submit_mags:
#         mags['OPTIONAL_FIELDS'] = None
    
#     # Add assembly, bins, mags to the dict
#     if submit_assembly or submit_bins or submit_mags:
#         config['ASSEMBLY'] = assembly
#     if submit_bins or submit_mags:
#         config['BINS'] = bins
#     if submit_mags:
#         config['MAGS'] = mags

#     # BAM files if we need to calculate coverages
#     if submit_assembly or submit_bins or submit_mags:
#         if coverage_from_bam:
#             assert known_coverage == False
#             config['BAM_FILES'] = [""]
#         elif known_coverage:
#             assert coverage_from_bam == False
#             if submit_assembly:
#                 config['ASSEMBLY']['COVERAGE'] = ""
#             if submit_bins:
#                 config['BINS']['COVERAGE_FILE'] = ""
#         else:
#             raise ValueError("Either coverage_from_bam or known_coverage must be set to True")

#     return config
