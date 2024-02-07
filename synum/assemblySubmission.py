import os
import csv
import requests
import gzip
import shutil
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth

from synum import utility, loggingC
from synum.utility import from_config
from synum.statConf import staticConfig
from synum.webinWrapper import webin_cli

def __prep_coassembly_samplesheet(config: dict,
                                  outdir: str,
                                  origin_samples: list) -> str:
    """
    Prepares the samplesheet for a co-assembly.

    Args:
        config (dict): The configuration dictionary.
        outdir (str): The directory where the samplesheet will be written.
        staticConfig (staticConfig, optional): The static configuration object. Defaults to staticConfig.

    Returns:
        str: The path to the samplesheet.
    """
    loggingC.message(f">Preparing assembly samplesheet...", threshold=0)

    sample_alias = from_config(config, 'ASSEMBLY', 'ASSEMBLY_NAME').replace(' ', '_')

    # Create XML tree
    root = ET.Element("SAMPLE_SET")
    sample = ET.SubElement(root, "SAMPLE", alias=sample_alias)

    title = ET.SubElement(sample, "TITLE")
    title.text = from_config(config, 'ASSEMBLY', 'ASSEMBLY_NAME')

    sample_name = ET.SubElement(sample, "SAMPLE_NAME")
    taxon_id = ET.SubElement(sample_name, "TAXON_ID")
    taxon_id.text = from_config(config, 'METAGENOME_TAXID')
    scientific_name = ET.SubElement(sample_name, "SCIENTIFIC_NAME")
    scientific_name.text = from_config(config, 'METAGENOME_SCIENTIFIC_NAME')


    sample_attributes = ET.SubElement(sample, "SAMPLE_ATTRIBUTES")

    # Create SAMPLE_ATTRIBUTE elements
    attributes_data = [
        ("collection date", (from_config(config, 'ASSEMBLY', 'collection date'))),
        ("geographic location (country and/or sea)", from_config(config, 'ASSEMBLY', 'geographic location (country and/or sea)')),
        ("sample composed of", ','.join(origin_samples)),
    ]

    assembly_dict = from_config(config, 'ASSEMBLY')
    if 'ADDITIONAL_SAMPLESHEET_FIELDS' in assembly_dict:
        if not assembly_dict['ADDITIONAL_SAMPLESHEET_FIELDS'] is None:
            for key, value in assembly_dict['ADDITIONAL_SAMPLESHEET_FIELDS'].items():
                attributes_data.append([key, value])

    for tag, value in attributes_data:
        sample_attribute = ET.SubElement(sample_attributes, "SAMPLE_ATTRIBUTE")
        tag_element = ET.SubElement(sample_attribute, "TAG")
        tag_element.text = tag
        value_element = ET.SubElement(sample_attribute, "VALUE")
        value_element.text = value

    # Write XML to file
    outpath = os.path.join(outdir, "coassembly_samplesheet.xml")
    tree = ET.ElementTree(root)
    with open(outpath, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=False)

    loggingC.message(f"\t...written to {os.path.abspath(outpath)}", threshold=0)

    return outpath


def __submit_coassembly_samplesheet(sample_xml: str,
                                    staging_dir: str,
                                    logging_dir: str,
                                    url):
    """
    Uploads the samplesheet to ENA.

    Args:
        sample_xml (str): The path to the samplesheet.
        staging_dir (str): The staging directory.
        logging_dir (str): The logging directory.
        url (str): The ENA API URL.

    Returns:
        str: The accession number of the uploaded sample.
    """

    submission_xml = os.path.join(staging_dir, "co_assembly_samplesheet_submission.xml")
    utility.build_sample_submission_xml(submission_xml,
                                hold_until_date=None)

    receipt_path = os.path.join(logging_dir, "assembly_samplesheet_receipt.xml")
    usr, pwd = utility.get_login()

    loggingC.message(f">Trying to submit samplesheet through ENA API.", threshold=0)
    response = requests.post(url,
                files={
                    'SUBMISSION': open(submission_xml, "rb"),
                    'SAMPLE': open(sample_xml, "rb"),
                }, auth=HTTPBasicAuth(usr, pwd))
    loggingC.message("\tHTTP status: "+str(response.status_code), threshold=1)
    utility.api_response_check(response)

    with open(receipt_path, 'w') as f:
        f.write(response.text)
    accession = utility.read_receipt(receipt_path)

    return accession


def __prep_assembly_manifest(config: dict,
                             outdir: str,
                             depth_files,
                             run_accessions,
                             sample_accession: str,
                             fasta_path: str,
                             threads=4) -> str:
    """
    Prepares the assembly manifest.

    Args:
        config (dict): The configuration dictionary.
        outdir (str): The directory where the manifest will be written.
        depth_files (str): The path to the depth files.
        sample_accession (str): The accession number of the sample.
        fasta_path (str): The path to the fasta file.
        threads (int, optional): The number of threads to use. Defaults to 4.
        
    Returns:
        Tuple[str, str]: The upload directory and the path to the manifest file.
    """
    loggingC.message(f">Preparing assembly manifest file", threshold=0)
    
    # Determine coverage
    if depth_files is None:
        COVERAGE = utility.from_config(config, 'ASSEMBLY', 'COVERAGE_VALUE')
    else:
        COVERAGE = utility.calculate_coverage(depth_files,
                                            threads=threads)

    # Write manifest
    PLATFORM = utility.from_config(config, 'SEQUENCING_PLATFORMS')
    if isinstance(PLATFORM, list):
        PLATFORM = ",".join(PLATFORM)

    assert type(run_accessions) is list
    run_accessions = ",".join(run_accessions)

    rows = [
        [ 'STUDY', utility.from_config(config, 'STUDY') ],
        [ 'SAMPLE', sample_accession ],
        [ 'ASSEMBLYNAME', utility.from_config(config, 'ASSEMBLY','ASSEMBLY_NAME') ],
        [ 'ASSEMBLY_TYPE', staticConfig.sequence_assembly_type ],
        [ 'COVERAGE', COVERAGE ],
        [ 'PROGRAM', utility.from_config(config, 'ASSEMBLY','ASSEMBLY_SOFTWARE') ],
        [ 'PLATFORM', PLATFORM ],
        [ 'MOLECULETYPE', staticConfig.assembly_molecule_type],
        [ 'RUN_REF', run_accessions ],
        [ 'FASTA', os.path.basename(fasta_path)],   
    ]

    assembly_dict = from_config(config, 'ASSEMBLY')
    if 'ADDITIONAL_MANIFEST_FIELDS' in assembly_dict:
        if not assembly_dict['ADDITIONAL_MANIFEST_FIELDS'] is None:
            for key, value in assembly_dict['ADDITIONAL_MANIFEST_FIELDS'].items():
                rows.append([key, value])

    manifest_path = os.path.join(outdir, "MANIFEST")
    with open(manifest_path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    return manifest_path


def submit_assembly(config: dict,
                    staging_dir: str,
                    logging_dir: str,
                    depth_files: str,
                    sample_accessions_data,
                    run_accessions,
                    threads: int = 4,
                    test: bool = True,
                    submit: bool = True,
                    staticConfig=staticConfig):
    """
    Submits the assembly to ENA.

    Args:

    Returns:
        Tuple[str, str]: The assembly sample accession and the assembly
        analysis accession. The sample succession will refer to a biological
        sample in case of a non-co-assembly and to a virtual sample in case of
        a co-assembly. 
    """

    if test:
        url = staticConfig.ena_test_dropbox_url
    else:
        url = staticConfig.ena_dropbox_url

    loggingC.message(f">Preparing assembly submission directory", threshold=1)
    assembly_submission_dir = os.path.join(staging_dir, "assembly_submission")
    os.makedirs(assembly_submission_dir, exist_ok=False)

    # If there is multiple samples referenced, then this is a co-assembly
    # and we need to create a samplesheet and upload it
    origin_samples = [x['accession'] for x in sample_accessions_data]
    assert type(origin_samples) is list
    if len(origin_samples) > 1:
        loggingC.message(f">Multiple SAMPLE_REFS in the config file mean this is a co-assembly", threshold=0)
        loggingC.message(f">For a co-assembly, a virtual sample object will be created in ENA", threshold=0)
        ## make a directory for the samplesheet submission
        sample_submission_dir = os.path.join(assembly_submission_dir, "co_assembly_sample")
        os.makedirs(sample_submission_dir, exist_ok=False)
        ## add a logging directory
        sample_logging_dir = os.path.join(logging_dir, "co_assembly_sample")
        os.makedirs(sample_logging_dir, exist_ok=False)
        ## make xml and submit

        samplesheet_path = __prep_coassembly_samplesheet(config,
                                                         sample_submission_dir,
                                                         origin_samples)
        assembly_sample_accession = __submit_coassembly_samplesheet(samplesheet_path,
                                                           sample_submission_dir,
                                                           sample_logging_dir,
                                                           url)
    else:
        assembly_sample_accession = origin_samples[0]

    # Upload the actual assembly
    ## make a directory and stage the fasta file
    fasta_submission_dir = os.path.join(assembly_submission_dir, "fasta")
    os.makedirs(fasta_submission_dir, exist_ok=False)

    fasta_path, gzipped = utility.check_fasta(from_config(config, 'ASSEMBLY', 'FASTA_FILE'))
    gzipped_fasta_path = os.path.join(fasta_submission_dir, f"assembly_upload{staticConfig.zipped_fasta_extension}")
    if not gzipped:
        loggingC.message(f">Gzipping assembly fasta file", threshold=0)
        with open(fasta_path, 'rb') as f_in:
            with gzip.open(gzipped_fasta_path, 'wb', compresslevel=5) as f_out:
                f_out.writelines(f_in)
    else:
        shutil.copyfile(fasta_path, gzipped_fasta_path)
    ## add a logging directory
    fasta_logging_dir = os.path.join(logging_dir, "assembly_fasta")
    os.makedirs(fasta_logging_dir, exist_ok=False)
    ## make a manifest and submit
    manifest_path = __prep_assembly_manifest(config,
                                             fasta_submission_dir,
                                             depth_files,
                                             run_accessions,
                                             assembly_sample_accession,
                                             gzipped_fasta_path,
                                             threads=threads)

    loggingC.message(f">Using ENA Webin-CLI to submit assembly.", threshold=0)
    assembly_name = utility.from_config(config, 'ASSEMBLY','ASSEMBLY_NAME')
    usr, pwd = utility.get_login()
    receipt, accession = webin_cli(manifest=manifest_path,
                                   inputdir=fasta_submission_dir,
                                   outputdir=fasta_logging_dir,
                                   username=usr,
                                   password=pwd,
                                   subdir_name=assembly_name,
                                   submit=submit,
                                   test=test)
    
    # Parse the receipt
    assembly_fasta_accession = utility.read_receipt(receipt)

    assembly_accession_file = os.path.join(logging_dir, "assembly_preliminary_accession.txt")
    with open(assembly_accession_file, 'w') as f:
        f.write(assembly_fasta_accession)

    print(f"\n>The preliminary(!) assembly accession has been written to {os.path.abspath(assembly_accession_file)}\n")

    return assembly_sample_accession, assembly_fasta_accession


