import csv
import os
import requests
from tqdm import tqdm
import shutil
import gzip
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth

from synum import loggingC, utility
from synum.webinWrapper import webin_cli
from synum.statConf import staticConfig

# def __report_tax_issues(issues):
#     """
#     Reports the issues encountered when trying to determine the taxonomy
#     of metagenome bins automatically.

#     Args:
#         issues (list): A list of dictionaries with the issues encountered.
#     """
#     err = f"\nERROR: Unable to determine taxonomy for {len(issues)} bins:"
#     loggingC.message(err, threshold=-1)
#     problematic_bins = [x['mag_bin'] for x in issues]
#     problematic_bins = set(problematic_bins)
#     msg = '\n'.join(problematic_bins)
#     loggingC.message(msg, threshold=0)
#     msg = f"Please manually enter taxonomy data for these bins into a .tsv file and specify it in the MANUAL_TAXONOMY_FILE field in the config file."
#     loggingC.message(msg, threshold=0) 
#     msg = f"\nTaxonomy issues are:"
#     loggingC.message(msg, threshold=0)
#     for i in issues:
#         mag = i['mag_bin']
#         level = i['level']
#         classification = i['classification']
#         suggestions = i['suggestions']
#         if len(i['suggestions']) == 0:
#             loggingC.message(f"MAG {mag} - no suggestions found (classified as {level} {classification})", threshold=0)
#         else:
#             loggingC.message(f"MAG {mag} - multiple suggestions found (classified as {level} {classification})", threshold=0)
#             loggingC.message("\tSuggestions are:", threshold=0)
#             for s in suggestions:
#                 loggingC.message(f"\t{s['taxId']}\t{s['scientificName']}", threshold=0)
#     exit(1)


# def query_ena_taxonomy(level: str,
#                          domain: str,
#                          classification: str,
#                          filtered: bool = True) -> list:
#     """ 
#     Based on the query string, use the ENA REST API to get a suggestion for the
#     taxonomy.

#     Args:
#         level (str): The taxonomic level of the query string.
#         domain (str): The domain of the query string.
#         classification (str): The query string.
#         filtered (bool, optional): If True, only return the best suggestion.
#             Defaults to True.

#     Returns:
#         list: A list of dictionaries with the suggestions from the ENA REST API.
#     """
#     # If we know the species we just query for that.
#     if level == 'species':
#         query = classification
#     # If we know the genus get a "<genus> sp." name
#     elif level == 'genus':
#         query = f"{classification} sp."
#     # If we only know the domain, we get "<uncultured> domain"
#     elif level == 'domain':
#         if domain == 'Archaea':
#             query = 'uncultured archaeon'
#         elif domain == 'Bacteria':
#             query = 'uncultured bacterium'
#         else:
#             err = f"\nERROR: Encountered unknown domain {domain} for a mag bin. Please check your NCBI taxonomy files."
#             loggingC.message(err, threshold=-1)
#             exit(1)
#     # If we know only something between domain and genus then we get
#     # "<classification> bacterium" / "<classification> archeon"
#     else:
#         if domain == 'Archaea':
#             dstring = 'archaeon'
#         elif domain == 'Bacteria':
#             dstring = 'bacterium'
#         elif domain == 'metagenome':
#             dstring = 'metagenome'
#         else:
#             err = f"\nERROR: Encountered unknown domain {domain}"
#             loggingC.message(err, threshold=-1)
#             exit(1)
#         if domain == 'metagenome':
#             query = classification
#         else:
#             query = f"{classification} {dstring}"    
    
#     url = f"https://www.ebi.ac.uk/ena/taxonomy/rest/suggest-for-submission/{query}"
#     response = requests.get(url)
#     if response.status_code == 200:
#         suggestions = response.json()
#         result = []
#         for suggestion in suggestions:
#             tax_id = suggestion.get("taxId", "N/A")
#             scientific_name = suggestion.get("scientificName", "N/A")
#             display_name = suggestion.get("displayName", "N/A")
#             taxdata = {"tax_id": tax_id, "scientificName": scientific_name, "displayName": display_name}
#             # If we don't filter we want all results
#             if not filtered:
#                 result.append(taxdata)
#             # For genus level we want the "is species of this genus" result
#             elif level == 'genus':
#                 if scientific_name.endswith('sp.'):
#                     result.append(taxdata)
#             # For species, we want the result that is the species name (no subspecies)
#             # It might have something like "Candidatus" in front so we don't exclude that
#             elif level == 'species':
#                 if scientific_name.endswith(classification):
#                     result.append(taxdata)
#             # For all other cases we want the "<classification> <domain>" taxon.
#             else:
#                 if scientific_name.endswith('archaeon') or scientific_name.endswith('bacterium') or level == 'metagenome':
#                     result.append(taxdata)                  
#         return result
#     else:
#         err = f"\nERROR: Trying to fetch taxonomy suggestion for {level}: {classification} (domain: {domain}) but ENA REST API returned status code {response.status_code}"
#         loggingC.message(err, threshold=-1)
#         loggingC.message(f"Attempted query was {url}", threshold=0)
#         exit(1)



def __calculate_bin_coverage(fasta: str,
                             depth_files: list,
                             threads=4) -> float:
    """
    Extract the names of contigs in the bin and calculate the bin coverage
    based on the depth files.

    Args:
        fasta (str): Path to the fasta file of the bin.
        depth_files (list): A list of paths to the depth files.
        threads (int, optional): Number of threads to use for samtools. Defaults to 4.

    Returns:
        float: The average coverage of the contigs in the bin.
    """
    # Extract the names of all contigs from the fasta file
    contig_names = []
    with open(fasta, 'r') as f:
        for line in f:
            if line.startswith('>'):
                contig_names.append(line.strip().split(' ')[0][1:])
    # Get the average coverage of the contigs of this bin
    coverage = utility.calculate_coverage(depth_files,
                                          contig_names,
                                          threads=threads,
                                          silent=True)
    
    return coverage


# def __read_ncbi_taxonomy(ncbi_taxonomy_file: str) -> dict:
#     """
#     Read the output of GTDB-TKs 'gtdb_to_ncbi_majority_vote.py' or a file using
#     the format described in README.md and return a dictionary with a taxid and a
#     scientific name for each genome.
#     Important note: The output of GTDB-TKs 'gtdb_to_ncbi_majority_vote.py' script
#     might miss some genome bins which didn't get GTDB classifications.

#     Args:
#         ncbi_to_taxonomy_file (str): Output files of GTDB-TKs
#             'gtdb_to_ncbi_majority_vote.py' script or NCBI taxonomy file with a
#             the columns 'Bin_id' and 'NCBI_taxonomy'.

#     Returns:
#         dict: A dictionary with a taxid and a scientific name for each genome. 
#     """
#     result = {}
#     with open(ncbi_taxonomy_file, 'r') as f:
#         reader = csv.reader(f, delimiter='\t')
#         header = next(reader) #skip header
#         if header == staticConfig.gtdb_majority_vote_columns.split(';'):
#             gtdb_majvote_output = True
#         else:
#             gtdb_majvote_output = False
#     if gtdb_majvote_output:
#         with open(ncbi_taxonomy_file, 'r') as f:
#             reader = csv.reader(f, delimiter='\t')
#             next(reader) #skip header
#             for row in reader:
#                 mag_bin = row[0].strip()
#                 lowest_ncbi_name = row[2].strip().split(';')
#                 result[mag_bin] = lowest_ncbi_name
#     else:
#         with open(ncbi_taxonomy_file, 'r') as f:
#             reader = csv.DictReader(f, delimiter='\t')
#             for row in reader:
#                 mag_bin = row["Bin_id"].strip()
#                 taxonomy_string = row["NCBI_taxonomy"].strip()
#                 lowest_ncbi_name = taxonomy_string.split(';')
#                 result[mag_bin] = lowest_ncbi_name
#     return result


# def __best_classifications(ncbi_classifications: dict) -> dict:
#     """
#     For each bin, find the best classification string. This is the classification
#     string on the lowest level that is not empty.

#     Args:
#         ncbi_classifications (dict): A dictionary with a list of classification strings
#         for each bin.

#     Returns:
#         dict: A dictionary with the best classification string for each bin.
#     """
#     result = {}
#     levels = staticConfig.taxonomic_levels.split(';')
#     for mag_bin, clist in ncbi_classifications.items():
#         # Check if we have an "unclassified" bin here
#         if len(clist) == 1:
#             clasf = clist[0]
#             if clasf == 'Unclassified Bacteria':
#                 result[mag_bin] = {
#                     'level': 'domain',
#                     'classification': 'Bacteria',
#                     'domain': 'Bacteria',
#                 }
#             elif clasf == 'Unclassified Archaea':
#                 result[mag_bin] = {
#                     'level': 'domain',
#                     'classification': 'Archaea',
#                     'domain': 'Archaea',
#                 }
#             else:
#                 err = f"\nERROR: Found unclassified bin {mag_bin} with unknown classification {clasf}. Please check your NCBI taxonomy files."
#                 loggingC.message(err, threshold=-1)
#                 exit(1)
#             loggingC.message(f">INFO: Bin {mag_bin} is unclassified.", threshold=1)
#         else:
#             # Iterate through classification strings until we find a valid one
#             for cstring, level in zip(reversed(clist), levels):
#                 if len(cstring) < 4: # no classification on this level
#                     continue
#                 break
#             # If this is unclassified we need to include some padding
#             if cstring.startswith('Unclassified'):
#                 cstring = '___'+cstring
#                 clist[0] = '___'+clist[0]
#             result[mag_bin] = {
#                 'level': level, 
#                 'classification': cstring[3:],
#                 'domain': clist[0][3:]
#             }
#     return result


# def __taxonomic_classification(ncbi_taxonomy_files: list) -> dict:
#     """
#     Read the output of GTDB-TKs 'gtdb_to_ncbi_majority_vote.py' script or
#     a similarly structured file and return a dictionary with a taxid and a
#     scientific name for each genome.
    
#     Args:
#         ncbi_to_taxonomy_file (str): Output files of GTDB-TKs
#             'gtdb_to_ncbi_majority_vote.py' script or NCBI taxonomy file with a
#             similar structure.

#     Returns:
#         dict: A dictionary with a taxid and a scientific name for each genome.
#     """
#     all_classifications = {}
#     for f in ncbi_taxonomy_files:
#         ncbi_classifications = __read_ncbi_taxonomy(f)
#         best_ncbi_classifications = __best_classifications(ncbi_classifications)
#         all_classifications.update(best_ncbi_classifications)
#     return all_classifications


# def __read_manual_taxonomy_file(manual_taxonomy_file: str) -> dict:
#     """
#     Read a manual taxonomy file and return a dictionary with the taxid and
#     scientific name for each bin.

#     Args:
#         manual_taxonomy_file (str): Path to the manual taxonomy file.

#     Returns:
#         dict: A dictionary with the taxid and scientific name for each bin.
#     """
#     result = {}
#     with open(manual_taxonomy_file, 'r') as f:
#         reader = csv.DictReader(f, delimiter='\t')
#         for row in reader:
#             mag_bin = row['Bin_id'].strip()
#             tax_id = row['Tax_id'].strip()
#             scientific_name = row["Scientific_name"].strip()
#             result[mag_bin] = {
#                 'tax_id': tax_id,
#                 'scientific_name': scientific_name,
#             }
#     return result

# def get_bin_taxonomy(config) -> dict:
#     """
#     Based on the NCBI taxonomy files and the manual taxonomy file, create a
#     dictionary with the taxid and scientific name for each bin.

#     Args:
#         config (dict): The config dictionary.

#     Returns:
#         dict: A dictionary with the taxid and scientific name for each bin.
#     """
#     loggingC.message(">Reading in bin taxonomy data", threshold=0)
#     # Extract data from config
#     ncbi_taxonomy_files = utility.optional_from_config(config, 'BINS', 'NCBI_TAXONOMY_FILES')
#     if ncbi_taxonomy_files == '': # Key not found in config
#         ncbi_taxonomy_files = []
#         loggingC.message(">No NCBI taxonomy files found in config.", threshold=0)
#     if not type(ncbi_taxonomy_files) == list:
#         ncbi_taxonomy_files = [ncbi_taxonomy_files]
#     bins_directory = utility.from_config(config, 'BINS', 'BINS_DIRECTORY')

#     # Make a list of all files in the bins directory
#     files = os.listdir(bins_directory)
#     bin_basenames = []
#     for f in files:
#         basename = utility.is_fasta(os.path.join(bins_directory, f))
#         if basename:
#             bin_basenames.append(basename)

#     # Read the taxnomy data from the MANUAL_TAXONOMY_FILE if it exists
#     upload_taxonomy_data = {}
#     try:
#         manual_taxonomy_file = utility.from_config(config,
#                                                    'BINS',
#                                                    'MANUAL_TAXONOMY_FILE',
#                                                    supress_errors=True)
#         loggingC.message(f">Reading manual taxonomy file {os.path.basename(manual_taxonomy_file)}", threshold=0)
#     except:
#         manual_taxonomy_file = 'manual_taxonomy_file_doesnt_exist'
#         loggingC.message(">No manual taxonomy file found.", threshold=0)
#     if os.path.exists(manual_taxonomy_file):
#         if not manual_taxonomy_file == 'manual_taxonomy_file_doesnt_exist':
#             upload_taxonomy_data = __read_manual_taxonomy_file(manual_taxonomy_file)

#     # Make a dictionary for the taxonomies based on the taxonomy files
#     annotated_bin_taxonomies = __taxonomic_classification(ncbi_taxonomy_files)


#     # Make sure that for each bin showing up in the taxonomy files we have a 
#     # corresponding fasta file in bin_files
#     from_taxonomies = set(upload_taxonomy_data.keys())
#     from_taxonomies.update(set(annotated_bin_taxonomies.keys()))
#     bin_basenames_set = set(bin_basenames)
#     only_bin_basenames = bin_basenames_set.difference(from_taxonomies)
#     only_taxonomies = from_taxonomies.difference(bin_basenames_set)
#     if len(only_bin_basenames) > 0:
#         err = f"\nERROR: The following bins were found in the bins directory but not in the taxonomy files:"
#         loggingC.message(err, threshold=-1)
#         for b in only_bin_basenames:
#             msg = f"\t{b}"
#             loggingC.message(msg, threshold=-0)
#         exit(1)
#     if len(only_taxonomies) > 0:
#         err = f"\nERROR: The following bins were found in the taxonomy files but not in the bins directory:"
#         loggingC.message(err, threshold=-1)
#         for b in only_taxonomies:
#             msg = f"\t{b}"
#             loggingC.message(msg, threshold=-1)
#         exit(1)
#     only_fasta = set(bin_basenames) - from_taxonomies
#     if len(only_fasta) > 0:
#         err = f"\nERROR: Tt in the taxonomy files:"
#         for b in only_fasta:
#             msg = f"\t{b}"
#             loggingC.message(msg, threshold=-1)
#         exit(1)

#     # Query the ENA API for taxids and scientific names for each bin
#     loggingC.message(">Querying ENA for taxids and scientific names for each bin.", threshold=0)

#     issues = []
#     for bin_name, taxonomy in tqdm(annotated_bin_taxonomies.items(), leave=False):
#         if bin_name in upload_taxonomy_data:
#             loggingC.message(f">INFO: Bin {bin_name} was found in the manual taxonomy file and will be skipped.", threshold=1)
#             continue
#         suggestions = query_ena_taxonomy(taxonomy['level'],
#                                            taxonomy['domain'],
#                                            taxonomy['classification'],
#                                            filtered=True)
#         if len(suggestions) == 1:
#             upload_taxonomy_data[bin_name] = {
#                 'scientific_name': suggestions[0]['scientificName'],
#                 'tax_id': suggestions[0]['tax_id'],
#             }
#         else:
#             all_ena_suggestions = query_ena_taxonomy(taxonomy['level'],
#                                                        taxonomy['domain'],
#                                                        taxonomy['classification'],
#                                                        filtered=False)

#             issues.append({
#                 'mag_bin': bin_name,
#                 'level': taxonomy['level'],
#                 'classification': taxonomy['classification'],
#                 'suggestions': all_ena_suggestions,
#             })

#     # Add any bins that only show up in the files to the issues as unclassified
#     for basename in bin_basenames:
#         if not basename in upload_taxonomy_data:
#             is_issue = False
#             for i in issues:
#                 if i['mag_bin'] == basename:
#                     is_issue = True
#             if is_issue:
#                 continue
#             issues.append({
#                 'mag_bin': basename,
#                 'level': 'unclassified',
#                 'classification': 'unclassified',
#                 'suggestions': [],
#             })

#     if len(issues) > 0:
#         __report_tax_issues(issues)
#         exit(1)

#     return upload_taxonomy_data

def get_bin_quality(config, silent=False) -> dict:
    """
    Based on CheckM output (or any other tsv with the columns 'Bin Id',
    'Completness' and 'Contamination'), create a dictionary with the
    completeness and contamination scores for each bin.

    Args:
        quality_file (str): Path to the quality file.

    Returns:
        dict: A dictionary with completeness and contamination scores for each
        bin. 
    """
    # Make a list of all files in the bins directory
    bins_directory = utility.from_config(config, 'BINS', 'BINS_DIRECTORY')
    files = os.listdir(bins_directory)
    bin_basenames = set()
    for f in files:
        basename = utility.is_fasta(os.path.join(bins_directory, f))
        if basename:
            bin_basenames.add(basename)
    # Get quality scores
    quality_file = utility.from_config(config, 'BINS', 'QUALITY_FILE')
    result = {}
    if not silent:
        msg = f">Reading bin quality file at {os.path.abspath(quality_file)}"
        loggingC.message(msg, threshold=0)
    with open(quality_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        headers = reader.fieldnames
        for row in reader:
            bin_id = row['Bin Id']
            completeness = float(row['Completeness'])
            contamination = float(row['Contamination'])
            result[bin_id] = {
                'completeness': completeness,
                'contamination': contamination,
            }

    # Check that the set of bins in the directory equals the set of bins in the quality file
    only_in_quality = set(result.keys()) - bin_basenames
    if len(only_in_quality) > 0:
        err = f"\nERROR: The following bins were found in the quality file but not in the bins directory:"
        loggingC.message(err, threshold=-1)
        for b in only_in_quality:
            msg = f"\t{b}"
            loggingC.message(msg, threshold=-1)
        msg = f"Quality file: {os.path.abspath(quality_file)}"
        loggingC.message(msg, threshold=-1)
        msg = f"Bins directory: {os.path.abspath(bins_directory)}"
        loggingC.message(msg, threshold=-1)
        exit(1)
    only_in_directory = bin_basenames - set(result.keys())
    if len(only_in_directory) > 0:
        err = f"\nERROR: The following bins were found in the bins directory but not in the quality file:"
        loggingC.message(err, threshold=-1)
        for b in only_in_directory:
            msg = f"\t{b}"
            loggingC.message(msg, threshold=-1)
        exit(1)

    loggingC.message(f"\t...found {len(result)} bins in bin quality file.", threshold=1)

    return result


def __prep_bins_samplesheet(config: dict,
                            assembly_sample_accession: str,
                            samples_submission_dir: str,
                            upload_taxonomy_data: dict) -> str:
    """
    Prepares an XML samplesheet for all bin samples.

    Args:
        config (dict): The config dictionary.
        assembly_sample_accession (str): Either the accession of a co-assembly
            virtual sample or the accession of the single biological sample
            which the assembly is based on.
        samples_submission_dir (str): The directory where the samplesheet will
            be written to.
        upload_taxonomy_data (dict): A dictionary with the taxid and scientific
            name for each bin.

    Returns:
        str: The path to the samplesheet.
    """
    loggingC.message(">Preparing bins samplesheet...", threshold=0)

    bin_quality = get_bin_quality(config)
    sequencing_platform = utility.from_config(config, 'SEQUENCING_PLATFORMS')
    if isinstance(sequencing_platform, list):
        sequencing_platform = ",".join(sequencing_platform)
    assembly_software = utility.from_config(config, 'ASSEMBLY', 'ASSEMBLY_SOFTWARE')
    completeness_software = utility.from_config(config, 'BINS', 'COMPLETENESS_SOFTWARE')
    binning_software = utility.from_config(config, 'BINS', 'BINNING_SOFTWARE')
    assembly_quality = staticConfig.bin_assembly_quality
    collection_date = utility.from_config(config, 'ASSEMBLY', 'collection date')
    geographic_location_country = utility.from_config(config, 'ASSEMBLY', 'geographic location (country and/or sea)')
    investigation_type = staticConfig.bin_investigation_type
    sample_derived_from = assembly_sample_accession
    metagenomic_source = utility.from_config(config, 'METAGENOME_SCIENTIFIC_NAME')
    sequencing_method = utility.from_config(config, 'SEQUENCING_PLATFORMS')
    if isinstance(sequencing_method, list):
        sequencing_method = ",".join(sequencing_method)

    # Define root element
    root = ET.Element("SAMPLE_SET")

    for bin_id in upload_taxonomy_data.keys():

        assembly_name = utility.from_config(config, 'ASSEMBLY', 'ASSEMBLY_NAME').replace(' ', '_')
        sample_alias = f"{assembly_name}_bin_{bin_id}_virtual_sample"
        sample_title = f"{assembly_name}_bin_{bin_id}_virtual_sample"
        
        tax_id = upload_taxonomy_data[bin_id]['tax_id']
        scientific_name = upload_taxonomy_data[bin_id]['scientific_name']

        completeness = str(bin_quality[bin_id]['completeness'])
        contamination = str(bin_quality[bin_id]['contamination'])

        # Create XML
        sample = ET.SubElement(root, "SAMPLE", alias=sample_alias)

        title = ET.SubElement(sample, "TITLE")
        title.text = sample_title

        sample_name = ET.SubElement(sample, "SAMPLE_NAME")
        taxon_id = ET.SubElement(sample_name, "TAXON_ID")
        taxon_id.text = str(tax_id)
        scientific_name = ET.SubElement(sample_name, "SCIENTIFIC_NAME")
        scientific_name.text = scientific_name

        sample_attributes = ET.SubElement(sample, "SAMPLE_ATTRIBUTES")
        
        # Add the attributes we specified above
        attribute_data = {
#            "project name": project_name,
            "sequencing method": sequencing_method,
            "assembly software": assembly_software,
            "completeness score": completeness,
            "completeness software": completeness_software,
            "contamination score": contamination,
            "binning software": binning_software,
            "assembly quality": assembly_quality,
            "investigation type": investigation_type,
            "collection date": collection_date,
            "geographic location (country and/or sea)": geographic_location_country,
            "sample derived from": sample_derived_from,
            "metagenomic source": metagenomic_source,
        }

        # Add additional attributes specified in the config bin section
        try:
            bin_additional_dict = utility.from_config(config, 'BINS', 'ADDITIONAL_SAMPLESHEET_FIELDS', supress_errors=True)
        except:
            bin_additional_dict = None
        if bin_additional_dict is not None:
            for key in bin_additional_dict.keys():
                if not bin_additional_dict[key] is None:
                    attribute_data[key] = bin_additional_dict[key]

        # Add additional attributes from assembly
        try:
            assembly_additional_dict = utility.from_config(config, 'ASSEMBLY', 'ADDITIONAL_SAMPLESHEET_FIELDS', supress_errors=True)
        except:
            assembly_additional_dict = None
        related_fields = [
            'broad-scale environmental context',
            'local environmental context',
            'environmental medium',
            'geographic location (latitude)',
            'geographic location (longitude)',
        ]
        if assembly_additional_dict is not None:
            for key in related_fields:
                if key in assembly_additional_dict.keys():
                    attribute_data[key] = assembly_additional_dict[key]

        # Add all attributes to the XML tree
        for key, value in attribute_data.items():
            if value:  # Only add attribute if value is not empty
                attribute = ET.SubElement(sample_attributes, "SAMPLE_ATTRIBUTE")
                ET.SubElement(attribute, "TAG").text = key
                ET.SubElement(attribute, "VALUE").text = value

    # Convert the XML structure to a string
    tree = ET.ElementTree(root)
    outpath = os.path.join(samples_submission_dir, "bins_samplesheet.xml")
    outpath = os.path.abspath(outpath)
    with open(outpath, 'wb') as f:
        tree.write(f, encoding='UTF-8', xml_declaration=False)

    loggingC.message(f"\t...written bins samplesheet to {outpath}", threshold=0)

    return outpath

def read_bin_samples_receipt(receipt_path: str) -> dict:
    """
    Reads the receipt file from the bin samplesheet upload and returns a
    dictionary with the bin names and their accession numbers.

    Args:
        receipt_path (str): Path to the receipt file.

    Returns:
        dict: A dictionary with the bin names and their accession numbers.
    """
    tree = ET.parse(receipt_path)
    root = tree.getroot()

    success = root.attrib['success']
    if success != 'true':
        err = f"\nERROR: Submission failed. Please consult the receipt file at {os.path.abspath(receipt_path)} for more information."
        loggingC.message(err, threshold=-1)
        exit(1)

    loggingC.message("\t...samplesheet upload was successful.", threshold=1)

    bin_to_accession = {}
    for sample in root.findall('.//SAMPLE'):
        alias = sample.attrib.get('alias')
        if alias is None:
            err = f"\nERROR: Submission failed. Didn't find alias for all bins in the receipt. Please check the receipt at {os.path.abspath(receipt_path)}."
            loggingC.message(err, threshold=-1)
            exit(1)
        ext_id = sample.find('EXT_ID')
        if ext_id is None:
            err = f"\nERROR: Submission failed. Didn't find EXT_ID for all bins in the receipt. Please check the receipt at {os.path.abspath(receipt_path)}."
            loggingC.message(err, threshold=-1)
            exit(1)
        accession = ext_id.attrib.get('accession')
        bin_to_accession[alias] = accession

    return bin_to_accession

def __submit_bins_samplesheet(sample_xml: str,
                              staging_dir: str,
                              logging_dir: str,
                              url: str) -> str:
    """
    Uploads the samplesheet to ENA.

    Args:
        sample_xml (str): Path to the samplesheet.
        staging_dir (str): Path to the staging directory.
        logging_dir (str): Path to the logging directory.
        url (str): The URL to the ENA dropbox.

    Returns:
        dict: A dictionary matching bin ids to accessions
    """

    # Make the submission XML
    submission_xml = os.path.join(staging_dir, 'bin_samplesheet_submission.xml')
    utility.build_sample_submission_xml(submission_xml,
                                        hold_until_date=None)
    
    # Submit
    loggingC.message(">Submitting bins samplesheet through ENA API.", threshold=0)
    receipt_path = os.path.join(logging_dir, "bins_samplesheet_receipt.xml")
    usr, pwd = utility.get_login()
    response = requests.post(url,
                files={
                    'SUBMISSION': open(submission_xml, "rb"),
                    'SAMPLE': open(sample_xml, "rb"),
                }, auth=HTTPBasicAuth(usr, pwd))
    loggingC.message(f"\tHTTP status: {response.status_code}", threshold=1)

    # Process response
    utility.api_response_check(response)
    with open(receipt_path, 'w') as f:
        f.write(response.text)
    bin_to_accession = read_bin_samples_receipt(receipt_path)

    return bin_to_accession


def __prep_bin_manifest(config: dict,
                        staging_directory: str,
                        bin_coverage: float,
                        bin_sample_accession: str,
                        run_accessions: list,
                        gzipped_fasta_path: str) -> str:
    """
    Creates a manifest file for a single bin inside the staging directory.

    Args:
        config (dict): The config dictionary.
        staging_directory (str): The directory where the manifest will be
            written to.
        bin_coverage (float): The coverage of the bin.
        bin_sample_accession (str): The accession number of the bin sample.
        gzipped_fasta_path (str): Path to the gzipped fasta file of the bin.

    Returns:
        str: The path to the manifest file.
    """
    loggingC.message(f">Preparing bin manifest in {staging_directory}...", threshold=1)

    sequencing_platform = utility.from_config(config, 'SEQUENCING_PLATFORMS')
    if isinstance(sequencing_platform, list):
        sequencing_platform = ",".join(sequencing_platform)

    if isinstance(run_accessions, list):
        run_accessions = ",".join(run_accessions)

    assembly_name = utility.from_config(config, 'ASSEMBLY', 'ASSEMBLY_NAME')
    assembly_name = assembly_name.replace(' ','_')
    bin_assembly_name = f"{assembly_name}_bin_{bin_sample_accession}"
    if len(bin_assembly_name) > staticConfig.max_assembly_name_length:
        # Cut characters from the beginning until the name fits
        bin_assembly_name = bin_assembly_name[-staticConfig.max_assembly_name_length:]

    rows = [
        ['STUDY', utility.from_config(config, 'STUDY')],
        ['SAMPLE', bin_sample_accession],
        ['ASSEMBLYNAME', bin_assembly_name],
        ['ASSEMBLY_TYPE', 'binned metagenome'],
        ['COVERAGE', bin_coverage],
        ['PROGRAM', utility.from_config(config, 'BINS', 'BINNING_SOFTWARE')],
        ['PLATFORM', sequencing_platform],
        ['MOLECULETYPE', staticConfig.assembly_molecule_type],
        ['RUN_REF', run_accessions],
        ['FASTA', os.path.basename(gzipped_fasta_path)]
    ]

    manifest_path = os.path.join(staging_directory, "MANIFEST")
    with open(manifest_path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    loggingC.message(f"\t...written bin manifest to {os.path.abspath(manifest_path)}", threshold=1)

    return manifest_path

def __stage_bin_submission(staging_directory: str,
                           bin_name: str,
                           bin_fasta: str,
                           config: dict,
                           bin_sample_accession: str,
                           run_accessions: list,
                           bin_coverage) -> None:
    """
    Prepares a bin submission by creating a manifest file inside the staging
    directory and copying the fasta file to the staging directory.

    Args:
        staging_directory (str): The directory where the manifest will be
            written to.
        bin_name (str): The name of the bin.
        bin_fasta (str): Path to the fasta file of the bin.
        config (dict): The config dictionary.
        bin_sample_accession (str): The accession number of the bin sample.
        bin_coverage (float): The coverage of the bin.

    Returns:
        str: The path to the manifest file.
    """
    
    # Stage the fasta file
    gzipped_fasta_path = os.path.join(staging_directory, "bin"+f"assembly_upload{staticConfig.zipped_fasta_extension}")
    if bin_fasta.endswith('.gz'):
        shutil.copyfile(bin_fasta, gzipped_fasta_path)
    else:
        with open(bin_fasta, 'rb') as f_in:
            with gzip.open(gzipped_fasta_path, 'wb', compresslevel=5) as f_out:
                f_out.writelines(f_in)

    # Make the MANIFEST file
    manifest_path = __prep_bin_manifest(config,
                                        staging_directory,
                                        bin_coverage,
                                        bin_sample_accession,
                                        run_accessions,
                                        gzipped_fasta_path)  

    return manifest_path          

    
def bin_coverage_from_depth(depth_files: str,
                              bin_name_to_fasta: dict,
                              threads: int = 4) -> dict:
    """
    Calculate coverage for each bin from depth files.

    Args:
        depth_files (str): Path to the depth files.
        bin_name_to_fasta (dict): Dictionary mapping bin names to fasta files.
        threads (int, optional): Number of threads to use for calculation. Defaults to 4.

    Returns:
        dict: Dictionary mapping bin names to coverage values.
    """
    loggingC.message(">Calculating coverage for each bin from depth files.", threshold=0)
    bin_coverages = {}
    for bin_name, bin_fasta in tqdm(bin_name_to_fasta.items(), leave=False):
        coverage = __calculate_bin_coverage(bin_fasta,
                                            depth_files,
                                            threads=threads)
        bin_coverages[bin_name] = coverage
    return bin_coverages


def bin_coverage_from_tsv(bin_coverage_file: str,
                          bin_names: dict) -> dict:
    """Reads coverage for each bin from a tsv file.

    Args:
        bin_coverage_file (str): The path to the tsv file containing the bin
            coverage data.
        bin_names (dict): A dictionary mapping bin names to their corresponding
            IDs.

    Returns:
        dict: A dictionary mapping bin names to their coverage values.
    """
    loggingC.message(">Reading coverage for each bin from tsv file.", threshold=0)
    bin_coverages = {}
    with open(bin_coverage_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            bin_name = row['Bin_id']
            coverage = float(row['coverage'])
            bin_coverages[bin_name] = coverage
    for known_name in bin_names:
        if not known_name in bin_coverages:
            err = f"\nERROR: Bin {known_name} was not found in the coverage file at {os.path.abspath(bin_coverage_file)}."
            loggingC.message(err, threshold=-1)
            exit(1)
    return bin_coverages
    

def get_bins_in_dir(bins_directory: str) -> list:
    """ 
    Get a dictionary mapping bin names to their corresponding fasta file paths in the given directory.

    Args:
        bins_directory (str): The directory containing the bin files.

    Returns:
        dict: A dictionary mapping bin names to their corresponding fasta file paths.
    """
    bin_files = os.listdir(bins_directory)
    bin_name_to_fasta = {}
    for f in bin_files:
        bin_name = utility.is_fasta(os.path.join(bins_directory, f))
        if bin_name is None:
            loggingC.message(f"\t...skipping {f} because it does not seem to be a fasta file.", threshold=0)
            continue
        bin_name_to_fasta[bin_name] = os.path.join(bins_directory, f)
    return bin_name_to_fasta


def submit_bins(config: dict,
                upload_taxonomy_data: dict,
                assembly_sample_accession: str,
                run_accessions,
                staging_dir: str,
                logging_dir: str,
                depth_files: list,
                bin_coverage_file: str,
                threads: int = 4,
                test: bool = True,
                submit: bool = True) -> tuple:
    """
    Submits a samplesheet for all metagenomic bins to the ENA. Then submits each
    bin as an individual analysis object using webin-cli.

    Args:
        config (dict): The config dictionary.
        upload_taxonomy_data (dict): A dictionary with the taxid and scientific
            name for each bin.
        assembly_sample_accession (str): Either the accession of a co-assembly
            virtual sample or the accession of the single biological sample
            which the assembly is based on.
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

    Returns:
        tuple: A tuple with the receipt paths and the accession numbers of the
            bins.
    """

    if test:
        url = staticConfig.ena_test_dropbox_url
    else:
        url = staticConfig.ena_dropbox_url
    
    # Extract data from config
    bins_directory = utility.from_config(config, 'BINS', 'BINS_DIRECTORY')


    # Make a list of all files in the bins directory and extract bin names
    loggingC.message(">Deriving bin names", threshold=1)
    bin_name_to_fasta = get_bins_in_dir(bins_directory)


    # Get the coverage for each bin file
    loggingC.message(">Deriving bin coverage", threshold=1)
    if not depth_files is None:
        bin_coverages = bin_coverage_from_depth(depth_files,
                                                bin_name_to_fasta,
                                                threads=threads)
    elif not bin_coverage_file is None:
        bin_coverages = bin_coverage_from_tsv(bin_coverage_file,
                                              bin_name_to_fasta.keys())
        

    # Make a samplesheet for all bins
    loggingC.message(">Making bin samplesheet", threshold=1)
    samples_submission_dir = os.path.join(staging_dir, 'bin_samplesheet')
    os.makedirs(samples_submission_dir, exist_ok=False)
    samplesheet = __prep_bins_samplesheet(config,
                                          assembly_sample_accession,
                                          samples_submission_dir,
                                          upload_taxonomy_data)
    
    # Upload the samplesheet
    loggingC.message(">Starting bin samplesheet upload", threshold=1)
    samples_logging_dir = os.path.join(logging_dir, 'bin_samplesheet')
    os.makedirs(samples_logging_dir, exist_ok=False)
    prefixbin_to_accession = __submit_bins_samplesheet(samplesheet,
                                                    samples_submission_dir,
                                                    samples_logging_dir,
                                                    url)
    # Remove the prefixes
    assembly_name = utility.from_config(config, 'ASSEMBLY', 'ASSEMBLY_NAME').replace(' ', '_')
    prefix_len = len(f"{assembly_name}_bin_")
    suffix_len= len(f"_virtual_sample")
    bin_to_accession = {}
    for suffix_bin_name, accession in prefixbin_to_accession.items():
        bin_name = suffix_bin_name[prefix_len:-suffix_len]
        bin_to_accession[bin_name] = accession
    
    # Stage the bins
    staging_directories = {}
    loggingC.message(">Staging bin submission sequences and manifests...", threshold=0)
    bin_manifests = {}
    for bin_name, bin_fasta in bin_name_to_fasta.items():
        bin_sample_accession = bin_to_accession[bin_name]
        staging_directory = os.path.join(staging_dir, f"bin_{bin_name}_staging")
        staging_directories[bin_name] = staging_directory
        os.makedirs(staging_directory, exist_ok=False)
        loggingC.message(f"\t...staging bin {bin_name}", threshold=1)
        bin_manifests[bin_name] = __stage_bin_submission(staging_directory,
                                                         bin_name,
                                                         bin_fasta,
                                                         config,
                                                         bin_sample_accession,
                                                         run_accessions,
                                                         bin_coverages[bin_name])

    # Submit the bins
    loggingC.message(f">Using ENA Webin-CLI to submit bins.", threshold=0)
    usr, pwd = utility.get_login()
    bin_receipts = {}
    bin_accessions = {}
    for bin_name, bin_staging_dir in staging_directories.items():
        bin_logging_dir = os.path.join(logging_dir, f"{bin_name}")
        os.makedirs(bin_logging_dir, exist_ok=False)
        bin_manifest = bin_manifests[bin_name]
        assembly_name = utility.from_config(config, 'ASSEMBLY','ASSEMBLY_NAME')
        subdir_name = assembly_name + '_' + bin_name

        bin_receipts[bin_name], bin_accessions[bin_name] = webin_cli(manifest=bin_manifest,
                                                                     inputdir=bin_staging_dir,
                                                                     outputdir=bin_logging_dir,
                                                                     username=usr,
                                                                     password=pwd,
                                                                     subdir_name=subdir_name,
                                                                     submit=submit,
                                                                     test=test)
    loggingC.message("\n>Bin submission completed!", threshold=0)

    # Process the results    
    loggingC.message(f">Bin receipt paths are:", threshold=1)
    for bin_name, bin_receipt in bin_receipts.items():
        loggingC.message(f"\t{bin_name}: {os.path.abspath(bin_receipt)}", threshold=1)

    bin_to_accession_file = os.path.join(logging_dir, 'bin_to_preliminary_accession.tsv')
    with open(bin_to_accession_file, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for bin_name, accession in bin_accessions.items():
            writer.writerow([bin_name, accession])

    loggingC.message(f"\n>The preliminary(!) accessions of your bins have been written to {os.path.abspath(bin_to_accession_file)}\n", threshold=0)