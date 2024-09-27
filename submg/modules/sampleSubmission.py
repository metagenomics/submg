import os

from . import loggingC, utility
from .utility import from_config, stamped_from_config
from .statConf import staticConfig

import requests

import xml.etree.ElementTree as ET

def __prep_samplesheet(config: dict,
                       staging_dir: str) -> str:
    """
    Prepares an XML file with the samplesheet for the biological samples.

    Args:
        config: The configuration dictionary.
        submission_dir: The directory where the samplesheet will be written.

    Returns:
        The path to the samplesheet.
    """
    tree_root = ET.Element('SAMPLE_SET')
    
    samples_data = from_config(config, 'NEW_SAMPLES')
    metagenome_scientific_name = from_config(config, 'METAGENOME_SCIENTIFIC_NAME')
    metagenome_taxid = from_config(config, 'METAGENOME_TAXID')

    for data in samples_data:
        tree_sample = ET.SubElement(tree_root, 'SAMPLE', alias=stamped_from_config(data, 'TITLE'))

        tree_title = ET.SubElement(tree_sample, 'TITLE')
        tree_title.text = from_config(data, 'TITLE')

        tree_sample_name = ET.SubElement(tree_sample, 'SAMPLE_NAME')
        ET.SubElement(tree_sample_name, 'TAXON_ID').text = metagenome_taxid
        ET.SubElement(tree_sample_name, 'SCIENTIFIC_NAME').text = metagenome_scientific_name

        tree_sample_attributes = ET.SubElement(tree_sample, 'SAMPLE_ATTRIBUTES')
        tree_attribute = ET.SubElement(tree_sample_attributes, 'SAMPLE_ATTRIBUTE')
        ET.SubElement(tree_attribute, 'TAG').text = 'geographic location (country and/or sea)'
        ET.SubElement(tree_attribute, 'VALUE').text = from_config(data, 'geographic location (country and/or sea)')
        tree_attribute = ET.SubElement(tree_sample_attributes, 'SAMPLE_ATTRIBUTE')
        ET.SubElement(tree_attribute, 'TAG').text = 'collection date'
        ET.SubElement(tree_attribute, 'VALUE').text = from_config(data, 'collection date')

        if 'ADDITIONAL_SAMPLESHEET_FIELDS' in data.keys() and data['ADDITIONAL_SAMPLESHEET_FIELDS'] is not None:
            for key, value in data['ADDITIONAL_SAMPLESHEET_FIELDS'].items():
                tree_attribute = ET.SubElement(tree_sample_attributes, 'SAMPLE_ATTRIBUTE')
                ET.SubElement(tree_attribute, 'TAG').text = key
                ET.SubElement(tree_attribute, 'VALUE').text = value
        
    # Convert the XML to a string
    tree = ET.ElementTree(tree_root)
    outpath = os.path.join(staging_dir, 'samplesheet.xml')

    with open(outpath, 'wb') as f:
        tree.write(f, encoding='UTF-8', xml_declaration=False)

    loggingC.message(f"\t...written samplesheet for biological samples to {os.path.abspath(outpath)}", threshold=0)

    return outpath


def __read_samplesheet_receipt(receipt_path: str) -> list:
    """
    Reads the receipt of the samplesheet upload.

    Args:
        receipt_path: The path to the receipt file.

    Returns:
        list: The accessions of the submitted samples.
    """
    tree = ET.parse(receipt_path)
    tree_root = tree.getroot()

    success = tree_root.attrib['success']
    if success != 'true':
        err = f"\nERROR: The submission of the biological samples failed. Consult the receipt file at {os.path.abspath(receipt_path)} for more information."
        loggingC.message(err, threshold=-1)
        exit(1)
    loggingC.message(f"\t...samplesheet upload was successful.", threshold=0)

    sample_accessions = []
    for sample in tree_root.iterfind('.//SAMPLE'):
        alias = sample.attrib.get('alias')
        ext_id = sample.find('EXT_ID')
        accession = sample.attrib.get('accession')
        external_accession = ext_id.attrib.get('accession')
        if alias is None is None or accession is None or external_accession is None:
            err = f"\nERROR: The submission of the biological samples failed. Consult the receipt file at {os.path.abspath(receipt_path)} for more information."
            loggingC.message(err, threshold=-1)
            exit(1)

        sample_accessions.append({
            'accession': accession,
            'external_accession': external_accession,
            'alias': alias,
        })

    return sample_accessions

    
def __submit_samplesheet(samplesheet: str,
                         staging_dir: str,
                         logging_dir: str,
                         url: str) -> list:
    """
    Submits the samplesheet to ENA.

    Args:
        samplesheet: The path to the samplesheet.
        staging_dir: The directory where the submission receipt will be written.
        logging_dir: The directory where the submission receipt will be written.
        url: The URL of the ENA API.

    Returns:
        list: The accessions of the submitted samples.
    """
    
    # Make the submission xml
    submission_xml = os.path.join(staging_dir, 'submission.xml')
    utility.build_sample_submission_xml(submission_xml,
                                        hold_until_date=None)
    
    # Submit
    receipt_path = os.path.join(logging_dir, 'submission_receipt.xml')
    usr, pwd = utility.get_login()

    loggingC.message(">Submitting biological samples samplesheet through ENA API", threshold=0)

    response = requests.post(url,
                             files={
                                'SUBMISSION': open(submission_xml, 'rb'),
                                'SAMPLE': open(samplesheet, 'rb'),},
                             auth=requests.auth.HTTPBasicAuth(usr, pwd))
    loggingC.message(f"\t...HTTP status: {response.status_code}", threshold=0)
    utility.api_response_check(response)

    # Write receipt
    with open(receipt_path, 'w') as f:
        f.write(response.text)
    loggingC.message(f"\t...written submission receipt to {os.path.abspath(receipt_path)}", threshold=0)

    # Get the accessions
    accessions = __read_samplesheet_receipt(receipt_path)

    return accessions


def submit_samples(config: dict,
                   staging_dir: str,
                   logging_dir: str,
                   test: bool  = True) -> list:
    """
    Submits the specified samples to ENA.

    Args:
        config: The configuration dictionary.
        staging_dir: The directory where the samplesheet will be written.
        logging_dir: The directory where the submission receipt will be written.
        test: Whether to use the test or production ENA API.

    Returns:
        list: The accessions of the submitted samples.
    """

    if test:
        url = staticConfig.ena_test_dropbox_url
    else:
        url = staticConfig.ena_dropbox_url

    # Make a samplesheet and stage it
    loggingC.message(">Preparing samplesheet for biological samples", threshold=0)
    sample_staging_dir = os.path.join(staging_dir, 'biological_samples')
    os.makedirs(sample_staging_dir, exist_ok=False)
    samplesheet = __prep_samplesheet(config,
                                     sample_staging_dir)
        
    
    # Upload the samplesheet
    loggingC.message(">Uploading samplesheet for biological samples", threshold=0)
    sample_logging_dir = os.path.join(logging_dir, 'biological_samples')
    os.makedirs(sample_logging_dir, exist_ok=False)
    sample_accessions = __submit_samplesheet(samplesheet,
                                     sample_staging_dir,
                                     sample_logging_dir,
                                     url=url)
    
    samples_accessions_file = os.path.join(sample_logging_dir, 'sample_preliminary_accessions.txt')
    with open(samples_accessions_file, 'w') as f:
        f.write("alias\taccession\texternal_accession\n")
        for sample in sample_accessions:
            f.write(f"{sample['alias']}\t{sample['accession']}\t{sample['external_accession']}\n")

    msg = f"\n>The preliminary(!) sample accessions have been written to {os.path.abspath(samples_accessions_file)}\n"
    loggingC.message(msg, threshold=0)

    return sample_accessions