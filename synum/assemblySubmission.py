import os
import csv
import requests
import gzip
import shutil
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth

from synum import utility
from synum.utility import from_config
from synum.statConf import staticConfig
from synum.webinWrapper import webin_cli

def __prep_coassembly_samplesheet(config: dict,
                                  outdir: str,
                                  verbose: int = 1,
                                  staticConfig=staticConfig) -> str:
    """
    Prepares the samplesheet for a co-assembly.

    Args:
        config (dict): The configuration dictionary.
        outdir (str): The directory where the samplesheet will be written.
        verbose (int, optional): The verbosity level. Defaults to 1.
        staticConfig (staticConfig, optional): The static configuration object. Defaults to staticConfig.

    Returns:
        str: The path to the samplesheet.
    """
    checklist = staticConfig.co_assembly_checklist

    if verbose > 0:
        print(f">Preparing assembly samplesheet...")

    sample_alias = from_config(config, 'ASSEMBLY', 'ASSEMBLY_NAME').replace(' ', '_')

    # Create XML tree
    root = ET.Element("SAMPLE_SET")
    sample = ET.SubElement(root, "SAMPLE", alias=sample_alias)

    title = ET.SubElement(sample, "TITLE")
    title.text = from_config(config, 'ASSEMBLY', 'ASSEMBLY_NAME')

    sample_name = ET.SubElement(sample, "SAMPLE_NAME")
    taxon_id = ET.SubElement(sample_name, "TAXON_ID")
    taxon_id.text = from_config(config, 'ASSEMBLY', 'TAXID')
    scientific_name = ET.SubElement(sample_name, "SCIENTIFIC_NAME")
    scientific_name.text = from_config(config, 'ASSEMBLY', 'SPECIES_SCIENTIFIC_NAME')


    sample_attributes = ET.SubElement(sample, "SAMPLE_ATTRIBUTES")
    # Create SAMPLE_ATTRIBUTE elements
    attributes_data = [
        ("collection date", str(from_config(config, 'ASSEMBLY', 'DATE'))),
        ("geographic location (country and/or sea)", from_config(config, 'ASSEMBLY', 'LOCATION')),
        ("ENA-CHECKLIST", checklist),
        ("sample composed of", ','.join(from_config(config, 'ASSEMBLY', 'SAMPLE_REFS'))),
    ]

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

    if verbose > 0:
        print(f"\t...written to {os.path.abspath(outpath)}")

    return outpath


def __submit_coassembly_samplesheet(sample_xml: str,
                                    staging_dir: str,
                                    logging_dir: str,
                                    url,
                                    verbose=1):
    """
    Uploads the samplesheet to ENA.

    Args:
        sample_xml (str): The path to the samplesheet.
        staging_dir (str): The staging directory.
        logging_dir (str): The logging directory.
        url (str): The ENA API URL.
        verbose (int, optional): The verbosity level. Defaults to 1.

    Returns:
        str: The accession number of the uploaded sample.
    """

    submission_xml = os.path.join(staging_dir, "co_assembly_samplesheet_submission.xml")
    utility.build_sample_submission_xml(submission_xml,
                                hold_until_date=None,
                                verbose=verbose)

    receipt_path = os.path.join(logging_dir, "assembly_samplesheet_receipt.xml")
    usr, pwd = utility.get_login()

    if verbose > 0:
        print(f">Trying to submit samplesheet through ENA API.")
    response = requests.post(url,
                files={
                    'SUBMISSION': open(submission_xml, "rb"),
                    'SAMPLE': open(sample_xml, "rb"),
                }, auth=HTTPBasicAuth(usr, pwd))
    if verbose>1:
        print("\tHTTP status: "+str(response.status_code))

    utility.api_response_check(response)

    with open(receipt_path, 'w') as f:
        f.write(response.text)
    accession = utility.read_receipt(receipt_path, verbose)

    return accession


def __prep_assembly_manifest(config: dict,
                             outdir: str,
                             depth_files,
                             sample_accession: str,
                             fasta_path: str,
                             threads=4,
                             verbose: int = 1) -> str:
    """
    Prepares the assembly manifest.

    Args:
        config (dict): The configuration dictionary.
        outdir (str): The directory where the manifest will be written.
        depth_files (str): The path to the depth files.
        sample_accession (str): The accession number of the sample.
        fasta_path (str): The path to the fasta file.
        threads (int, optional): The number of threads to use. Defaults to 4.
        verbose (int, optional): The verbosity level. Defaults to 1.
        
    Returns:
        Tuple[str, str]: The upload directory and the path to the manifest file.
    """
    if verbose > 0:
        print(f">Preparing assembly manifest file")
    
    # Determine coverage

    # Determine coverage from depth files
    COVERAGE = utility.calculate_coverage(depth_files,
                                          threads=threads,
                                          verbose=verbose)

    # Write manifest
    PLATFORM = utility.from_config(config, 'ASSEMBLY', 'PLATFORM')
    if isinstance(PLATFORM, list):
        PLATFORM = ",".join(PLATFORM)
    RUN_REFS = utility.from_config(config, 'ASSEMBLY', 'RUN_REFS')
    if isinstance(RUN_REFS, list):
        RUN_REFS = ",".join(RUN_REFS)

    rows = [
        [ 'STUDY', utility.from_config(config, 'STUDY') ],
        [ 'SAMPLE', sample_accession ],
        [ 'ASSEMBLYNAME', utility.from_config(config, 'ASSEMBLY','ASSEMBLY_NAME') ],
        [ 'ASSEMBLY_TYPE', staticConfig.sequence_assembly_type ],
        [ 'COVERAGE', COVERAGE ],
        [ 'PROGRAM', utility.from_config(config, 'ASSEMBLY','PROGRAM') ],
        [ 'PLATFORM', PLATFORM ],
        [ 'MOLECULETYPE', utility.from_config(config, 'ASSEMBLY','MOLECULE_TYPE')],
        # [ 'DESCRIPTION', utility.from_config(config, 'ASSEMBLY','DESCRIPTION')],
        [ 'RUN_REF', RUN_REFS ],
        [ 'FASTA', os.path.basename(fasta_path)],   
    ]

    manifest_path = os.path.join(outdir, "MANIFEST")
    with open(manifest_path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    return manifest_path


def submit_assembly(config: dict,
                    staging_dir: str,
                    logging_dir: str,
                    depth_files: str,
                    threads: int = 4,
                    verbose: int = 1,
                    test: bool = True,
                    submit: bool = True,
                    staticConfig=staticConfig):
    """
    Submits the assembly to ENA.

    Args:
        config (dict): The configuration dictionary.
        staging_dir (str): The staging directory.
        logging_dir (str): The logging directory.
        depth_files (str): The path to the depth files.
        threads (int, optional): The number of threads to use. Defaults to 4.
        verbose (int, optional): The verbosity level. Defaults to 1.
        test (bool, optional): Whether to use the test server. Defaults to True.
        submit (bool, optional): Whether to submit the assembly. Defaults to True.
        staticConfig (staticConfig, optional): The static configuration object. Defaults to staticConfig.

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

    if verbose > 1:
        print(f">Preparing assembly submission directory")
    assembly_submission_dir = os.path.join(staging_dir, "assembly_submission")
    os.makedirs(assembly_submission_dir, exist_ok=False)

    # If there is multiple samples referenced, then this is a co-assembly
    # and we need to create a samplesheet and upload it
    origin_samples = from_config(config, 'ASSEMBLY', 'SAMPLE_REFS')
    assert type(origin_samples) is list
    if len(origin_samples) > 1:
        if verbose > 0:
            print(f">Multiple SAMPLE_REFS in the config file mean this is a co-assembly")
            print(">For a co-assembly, a virtual sample objects will be created in ENA")
        ## make a directory for the samplesheet submission
        sample_submission_dir = os.path.join(assembly_submission_dir, "co_assembly_sample")
        os.makedirs(sample_submission_dir, exist_ok=False)
        ## add a logging directory
        sample_logging_dir = os.path.join(logging_dir, "co_assembly_sample")
        os.makedirs(sample_logging_dir, exist_ok=False)
        ## make xml and submit

        samplesheet_path = __prep_coassembly_samplesheet(config,
                                                         sample_submission_dir,
                                                         verbose)
        assembly_sample_accession = __submit_coassembly_samplesheet(samplesheet_path,
                                                           sample_submission_dir,
                                                           sample_logging_dir,
                                                           url,
                                                           verbose)
    else:
        assembly_sample_accession = origin_samples[0]

    # Upload the actual assembly
    ## make a directory and stage the fasta file
    fasta_submission_dir = os.path.join(assembly_submission_dir, "fasta")
    os.makedirs(fasta_submission_dir, exist_ok=False)

    fasta_path, gzipped = utility.check_fasta(from_config(config, 'ASSEMBLY', 'FASTA_FILE'))
    gzipped_fasta_path = os.path.join(fasta_submission_dir, f"assembly_upload{staticConfig.zipped_fasta_extension}")
    if not gzipped:
        if verbose > 0:
            print(f">Gzipping assembly fasta file")
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
                                             assembly_sample_accession,
                                             gzipped_fasta_path,
                                             threads=threads,
                                             verbose=verbose)

    if verbose>0:
        print(f">Using ENA Webin-CLI to submit assembly.\n")
    assembly_name = utility.from_config(config, 'ASSEMBLY','ASSEMBLY_NAME')
    usr, pwd = utility.get_login()
    receipt, accession = webin_cli(manifest=manifest_path,
                                   inputdir=fasta_submission_dir,
                                   outputdir=fasta_logging_dir,
                                   username=usr,
                                   password=pwd,
                                   subdir_name=assembly_name,
                                   submit=submit,
                                   test=test,
                                   verbose=verbose)
    
    # Parse the receipt
    assembly_fasta_accession = utility.read_receipt(receipt, verbose)

    assembly_accession_file = os.path.join(logging_dir, "assembly_preliminary_accession.txt")
    with open(assembly_accession_file, 'w') as f:
        f.write(assembly_fasta_accession)

    print(f"\n>The preliminary(!) assembly accession has been written to {os.path.abspath(assembly_accession_file)}\n")

    return assembly_sample_accession, assembly_fasta_accession


