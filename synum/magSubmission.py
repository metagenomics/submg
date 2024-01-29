import os
import csv

import xml.etree.ElementTree as ET

import gzip
import requests
import shutil

from requests.auth import HTTPBasicAuth
from synum import loggingC, utility, binSubmission, enaSearching
from synum.statConf import staticConfig


def __read_mag_metadata(single_assembly: bool,
                        mag_metadata_file: str) -> dict:
    """
    Reads the MAG metadata file and returns a metadata dict.

    Args:
        mag_metadata_file (str): Path to the MAG metadata file.

    Returns:
        dict: A dictionary with the metadata for each bin.
    """
    metadata = {}
    
    with open(os.path.abspath(mag_metadata_file), 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            bin_id = row['Bin_id']
            sample_id = row['Sample_id']
            quality_category = row['Quality_category']
            fasta_path = row['Fasta_path']
            flatfile_path = row['Flatfile_path']
            unlocalised_path = row['Unlocalised_path']

            for fieldname in ['Bin_id', 'quality_category', 'Flatfile_path']:
                if row['Bin_id'] is None:
                    problematic_bin = ""
                else:
                    problematic_bin = f"(Bin_id: {row['Bin_id']}"
                if row[fieldname] is None:
                    loggingC.message(f"\nERROR: {fieldname} is missing for a MAG in {os.path.abspath(mag_metadata_file)} {problematic_bin}", threshold=-1)
                    exit(1)

            if fasta_path is None and flatfile_path is None:
                loggingC.message(f"\nERROR: Neither fasta nor flatfile path is specified for a MAG {bin_id} in {os.path.abspath(mag_metadata_file)}", threshold=-1)
                exit(1)

            metadata[bin_id] = {
                'Sample_id': sample_id,
                'Quality_category': quality_category,
                'Flatfile_path': flatfile_path,
                'Fasta_path': fasta_path,
                'Unlocalised_path': unlocalised_path
            }
    
    return metadata


def __prep_mags_samplesheet(config: dict,
                            sample_accession_data: list,
                            mag_metadata: dict,
                            bin_taxonomy_data: dict,
                            assembly_sample_accession: str,
                            samples_submission_dir: str,
                            devtest: bool) -> str:
    """
    Prepares an XML samplesheet for all MAG samples assume all MAGs are derived
    from the same assembly.

    Args:
        config (dict): The config dictionary.
        sample_accession_data (list): A list of dictionaries with the sample
            accession data.
        mag_metadata (dict): A dictionary with the metadata for each MAG.
        bin_taxonomy_data (dict): A dictionary with the taxonomy data for each
            bin.
        assembly_sample_accession (str): The accession number of the assembly
            sample.
        samples_submission_dir (str): The directory where the samplesheet will
            be written to.

    Returns:
        str: The path to the samplesheet.
    """

    # Query data for all MAGs
    bin_quality = binSubmission.get_bin_quality(config)
    sequencing_platform = utility.from_config(config, 'SEQUENCING_PLATFORMS')
    if isinstance(sequencing_platform, list):
        sequencing_platform = ",".join(sequencing_platform)
    assembly_software = utility.from_config(config, 'ASSEMBLY', 'ASSEMBLY_SOFTWARE')
    completeness_software = utility.from_config(config, 'BINS', 'COMPLETENESS_SOFTWARE')
    binning_software = utility.from_config(config, 'BINS', 'BINNING_SOFTWARE')
    binning_parameters = utility.from_config(config, 'BINS', 'ADDITIONAL_SAMPLESHEET_FIELDS', 'binning parameters')
    project_name = utility.from_config(config, 'PROJECT_NAME')
    taxonomic_identity_marker = utility.from_config(config,
                                                    'BINS',
                                                    'ADDITIONAL_SAMPLESHEET_FIELDS',
                                                    'taxonomic identity marker')
    isolation_source = utility.from_config(config, 'ASSEMBLY', 'ISOLATION_SOURCE')
    collection_date = utility.from_config(config, 'ASSEMBLY', 'collection date')
    location_country = utility.from_config(config, 'ASSEMBLY', 'geographic location (country and/or sea)')
    location_latitude = utility.from_config(config, 'ASSEMBLY', 'geographic location (latitude)')
    location_longitude = utility.from_config(config, 'ASSEMBLY', 'geographic location (longitude)')
    env_context_broad = utility.from_config(config, 'ASSEMBLY', 'broad-scale environmental context')
    env_context_local = utility.from_config(config, 'ASSEMBLY', 'local environmental context')
    env_medium = utility.from_config(config, 'ASSEMBLY', 'environmental medium')
    assembly_name = utility.from_config(config, 'ASSEMBLY', 'ASSEMBLY_NAME').replace(' ', '_')
    metagenomic_source = enaSearching.search_scientific_name_by_sample(assembly_sample_accession,
                                                                       devtest)
    derived_from = ",".join([x['accession'] for x in sample_accession_data])


    root = ET.Element('SAMPLE_SET')
    for bin_id, metadata in mag_metadata.items():

        # Query general MAG data
        sample_alias = f"{assembly_name}_MAG_{bin_id}_virtual_sample"
        sample_title = f"{assembly_name}_MAG_{bin_id}_virtual_sample"
        tax_id = bin_taxonomy_data[bin_id]['tax_id']
        scientific_name  = bin_taxonomy_data[bin_id]['scientific_name']
        completeness = str(bin_quality[bin_id]['completeness'])
        contamination = str(bin_quality[bin_id]['contamination'])

        # Build XML
        sample = ET.SubElement(root, 'SAMPLE', alias=sample_alias)
        
        title = ET.SubElement(sample, 'TITLE')
        title.text = sample_title

        sample_name = ET.SubElement(sample, 'SAMPLE_NAME')

        taxon_id = ET.SubElement(sample_name, 'TAXON_ID')
        taxon_id.text = tax_id

        scientific_name = ET.SubElement(sample_name, 'SCIENTIFIC_NAME')
        scientific_name.text = scientific_name

        sample_attributes = ET.SubElement(sample, 'SAMPLE_ATTRIBUTES')

        # Collect the attributes we specified above
        attribute_data = {
            'project name': project_name,
            'assembly software': assembly_software,
            'completeness score': completeness,
            'contamination score': contamination,
            'binning software': binning_software,
            'assembly quality': metadata['Quality_category'],
            'binning parameters': binning_parameters,
            'taxonomic identity marker': taxonomic_identity_marker,
            'isolation_source' : isolation_source,
            'collection date': collection_date,
            'geographic location (country and/or sea)': location_country,
            'geographic location (latitude)': location_latitude,
            'geographic location (longitude)': location_longitude,
            'broad-scale environmental context': env_context_broad,
            'local environmental context': env_context_local,
            'environmental medium': env_medium,
            'sample derived from': derived_from,
            'metagenomic source': metagenomic_source,
        }

        # Collect any additional attributes specified in the config MAG section
        try:
            mag_additional_dict = utility.from_config(config, 'MAGS', 'ADDITIONAL_SAMPLESHEET_FIELDS')
        except:
            mag_additional_dict = None
        if mag_additional_dict is not None:
            for key in mag_additional_dict.keys():
                if not mag_additional_dict[key] is None:
                    attribute_data[key] = mag_additional_dict[key]
    
        # Add everything to the XML tree
        for key, value in attribute_data.items():
            if value: # Only add atrributes if values is not empty
                attribute = ET.SubElement(sample_attributes, 'SAMPLE_ATTRIBUTE')
                ET.SubElement(attribute, 'TAG').text = key
                ET.SubElement(attribute, 'VALUE').text = value

        # Convert the XML structure to a string
        tree = ET.ElementTree(root)
        outpath = os.path.join(samples_submission_dir, 'MAGs_samplesheet.xml')
        outpath = os.path.abspath(outpath)
        with open(outpath, 'wb') as f:
            tree.write(f, encoding='UTF-8', xml_declaration=False)

        loggingC.message(f"\t...written MAGs samplesheet to {outpath}", threshold=0)

        return outpath


def __submit_mags_samplesheet(samplesheet: str,
                              staging_dir: str,
                              logging_dir: str,
                              url: str) -> dict:
    """
    Uploads the MAGs samplesheet to ENA.

    Args:
        sample_xml (str): Path to the samplesheet.
        staging_dir (str): Path to the staging directory.
        logging_dir (str): Path to the logging directory.
        url (str): The URL to the ENA dropbox.

    Returns:
        dict: A dictionary matching MAG ids to acessions

    """
    # Make the submission XML
    submission_xml = os.path.join(staging_dir, 'mag_samplesheet_submission.xml')
    utility.build_sample_submission_xml(submission_xml,
                                        hold_until_date=None)
    
    # Submit
    loggingC.message(">Submitting MAGs samplesheet through ENA API.", threshold=0)
    receipt_path = os.path.join(logging_dir, "MAGs_samplesheet_receipt.xml")
    usr, pwd = utility.get_login()
    response = requests.post(url,
                             files={
                                 'SUBMISSION': open(submission_xml, 'rb'),
                                 'SAMPLE': open(samplesheet, 'rb')
                             }, auth=HTTPBasicAuth(usr, pwd))
    loggingC.message(f"\tHTTP status: {response.status_code}", threshold=1)

    # Process response
    utility.api_response_check(response)
    with open(receipt_path, 'wb') as f:
        f.write(response.content)
    bin_to_Accession = binSubmission.read_bin_samples_receipt(receipt_path)

    return bin_to_Accession


def __stage_mag_submission(metadata,
                           staging_directory: str,
                           mag_id: str,
                           config: dict,
                           mag_sample_accession: str,
                           coverage: float,
                           run_accessions: list) -> str:
    """
    """
    # Prepare some data
    assembly_name = utility.from_config(config, 'ASSEMBLY', 'ASSEMBLY_NAME')
    assembly_name = assembly_name.replace(' ', '_')
    mag_assembly_name = f"{assembly_name}_MAG_{mag_sample_accession}"

    sequencing_platform = utility.from_config(config, 'SEQUENCING_PLATFORMS')
    if isinstance(sequencing_platform, list):
        sequencing_platform = ",".join(sequencing_platform)

    if isinstance(run_accessions, list):
        run_accessions = ",".join(run_accessions)

    # Make the MANIFEST file
    loggingC.message(f">Preparing MAG manifest in {staging_directory}...", thereshold=1)
    rows = [
        ['STUDY', utility.from_config(config, 'STUDY')],
        ['SAMPLE', mag_sample_accession],
        ['ASSEMBLYNAME', mag_assembly_name],
        ['ASSEMBLY_TYPE', '‘Metagenome-Assembled Genome (MAG)’'],
        ['COVERAGE', coverage],
        ['PROGRAM', utility.from_config(config, 'BINS', 'BINNING_SOFTWARE')],
        ['PLATFORM', sequencing_platform],
        ['MOLECULETYPE', staticConfig.assembly_molecule_type],
        ['RUN_REF', run_accessions],
    ]

    # Stage the fasta- or flatfile and add them to rows
    if metadata['Flatfile_path'] is None:
        gzipped_fasta_path = os.path.join(staging_directory, "mag"+f"assembly_upload{staticConfig.zipped_fasta_extension}")
        fasta = metadata['Fasta_path']
        if fasta.endswith('.gz'):
            shutil.copyfile(fasta, gzipped_fasta_path)
        else:
            with open(fasta, 'rb') as f_in:
                with gzip.open(gzipped_fasta_path, 'wb', compresslevel=5) as f_out:
                    f_out.writelines(f_in)
        rows.append(['FASTA', gzipped_fasta_path])
    else:
        flatfile_target = os.path.join(staging_directory, "mag"+f"assembly_upload{staticConfig.emblff_extension}")
        shutil.copyfile(metadata['Flatfile_path'], flatfile_target)
        rows.append(['FLATFILE', flatfile_target])
    
    # Write the Manifest
    manifest_path = os.path.join(staging_directory, 'MANIFEST')
    with open(manifest_path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    return manifest_path



def submit_mags(single_assembly: bool,
                config: dict,
                assembly_sample_accession: str,
                sample_accession_data: list,
                run_accessions,
                bin_taxonomy_data: dict,
    #            bin_to_sample: dict,
                staging_dir: str,
                logging_dir: str,
                depth_files: str,
                bin_coverage_file: str,
                threads: int = 4,
                test: bool = True,
                submit: bool = True) -> tuple:
    """
    Submits a samplesheet for all MAGs to ENA. Then submits each MAG as an
    individual analysis object using webin-cli.
    
    Args:
        single_assembly: True if the MAG was derived from one single assembly.
        config (dict): The config dictionary.
        upload_taxonomy_data (dict): A dictionary with the taxid and scientific
            name for each bin.
        assembly_sample_accession (str): The accession number of the assembly
            sample.
        run_accessions (list): A list of accession numbers of the runs.
        staging_dir (str): The directory where the bins will be staged.
        logging_dir (str): The directory where the logs will be written to.
        depth_files (list): A list of paths to the depth files. Either this or
            bin_coverage_file must be specified.
        bin_coverage_file (str): Path to a tsv file with the coverage for each
            bin. Either this or depth_files must be specified.
        threads (int, optional): Number of threads to use for samtools. Defaults to 4.
        test (bool, optional): If True, the ENA dev server will be used
            instead of the production server. Defaults to True.
        submit (bool, optional): If True, the bins will be submitted to ENA.
            Otherwise only validation will happen. Defaults to True.
    """

    if not single_assembly:
        loggingC.message(f"\nERROR: Currently, this tool supports MAG submission is only for MAGs derived from a single assembly.", threshold=-1)
        exit(1)

    if test:
        url = staticConfig.ena_test_dropbox_url
    else:
        url = staticConfig.ena_dropbox_url
    
    # Extract data
    loggingC.message(">Reading MAG metadata", threshold=1)
    mag_metdata_file = utility.from_config(config, 'MAGS', 'MAG_METADATA_FILE')
    mag_metadata = __read_mag_metadata(single_assembly, mag_metdata_file)
    
    bins_directory = utility.from_config(config, 'BINS', 'BINS_DIRECTORY')
        
    # Get the coverage for each MAG
    loggingC.message(">Deriving MAG coverage", threshold=1)
    bin_files = binSubmission.get_bins_in_dir(bins_directory)
    if not depth_files is None:
        bin_coverages = binSubmission.bin_coverage_from_depth(depth_files,
                                                bin_files,
                                                threads=threads)
    elif not bin_coverage_file is None:
        bin_coverages = binSubmission.bin_coverage_from_tsv(bin_coverage_file,
                                              bin_files)
        
    # Make a samplesheet for all MAGs
    loggingC.message(">Making MAG samplesheet", threshold=1)
    samples_submission_dir = os.path.join(staging_dir, 'mag_samplesheet')
    os.makedirs(samples_submission_dir, exist_ok=False)
    samplesheet = __prep_mags_samplesheet(config,
                                          sample_accession_data,
                                          mag_metadata,
                                          bin_taxonomy_data,
                                          assembly_sample_accession,
                                          samples_submission_dir,
                                          test)


    # Upload the samplesheet
    loggingC.message(">Starting MAG samplesheet upload", threshold=1)
    samples_logging_dir = os.path.join(logging_dir, 'mag_samplesheet')
    os.makedirs(samples_logging_dir, exist_ok=False)
    prefixmag_to_accession = __submit_mags_samplesheet(samplesheet,
                                                       samples_logging_dir,
                                                       samples_submission_dir,
                                                       url)


    # Remove the prefiexes
    assembly_name = utility.from_config(config, 'ASSEMBLY', 'ASSEMBLY_NAME').replace(' ', '_')
    prefix_len = len(f"{assembly_name}_MAG_")
    suffix_len = len("_virtual_sample")
    mag_to_accession = {}
    for suffix_mag_name, accession in prefixmag_to_accession.items():
        mag_name = suffix_mag_name[prefix_len:-suffix_len]
        mag_to_accession[mag_name] = accession

    # Stage the MAGs
    bins_directory = utility.from_config(config, 'BINS', 'BINS_DIRECTORY')
    staging_directories = {}
    loggingC.message(">Staging MAG submission sequences and manifests...", threshold=0)
    mag_manifests = {}
    for mag_id in mag_metadata.keys():
        mag_sample_accession = mag_to_accession[mag_id]
        staging_directory = os.path.join(staging_dir, f"mag_{mag_id}_staging")
        staging_directories[mag_id] = staging_directory
        os.makedirs(staging_directory, exist_ok=False)
        coverage = bin_coverages[mag_id]
        metadata = mag_metadata[mag_id]
        loggingC.message(f"\t...staging MAG {mag_id}", threshold=1)
        mag_manifests[mag_id] = __stage_mag_submission(metadata,
                                                       staging_directory,
                                                       mag_id,
                                                       config,
                                                       mag_sample_accession,
                                                       coverage,
                                                       run_accessions)

    # Submit the MAGs
    loggingC.nmessage(f">Using ENA Webin-CLI to submit MAGS.\n", threshold=0)
    usr, pwd = utility.get_login()
    mag_receipts = {}
    mag_accessions = {}
    for mag_id, mag_staging_dir in staging_directories.items():
        mag_logging_dir = os.path.join(logging_dir, f"{mag_id}")
        os.makedirs(mag_logging_dir, exist_ok=False)
        mag_manifest = mag_manifests[mag_id]
        assembly_name = utility.from_config(config, 'ASSEMBLY','ASSEMBLY_NAME')
        subdir_name = assembly_name + '_' + mag_id
        mag_receipts[mag_id], mag_accessions[mag_id] = webin_cli(manifest=mag_manifest,
                                                                 inputdir=mag_staging_dir,
                                                                 outputdir=mag_logging_dir,
                                                                 username=usr,
                                                                 password=pwd,
                                                                 subdir_name=subdir_name,
                                                                 submit=submit)
    loggingC.message(f">MAG submission completed!", threshold=0)

    # Process the results
    loggingC.message(f">Mag receipt paths are", threshold=1)
    for mag_id, receipt in mag_receipts.items():
        loggingC.message(f"\t{mag_id}: {receipt}", threshold=1)

    bin_to_accession_file = os.path.join(logging_dir, 'mag_to_preliminary_accession.tsv')
    with open(bin_to_accession_file, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for mag_id, accession in mag_accessions.items():
            writer.writerow([mag_id, accession])

    loggingC.message(f">The preliminary(!) accessions of your MAGs have been written to {os.path.abspath(bin_to_accession_file)}", threshold=0)