import csv
import os

import requests
from tqdm import tqdm

import shutil
import gzip

import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth

from webinWrapper import webin_cli
import utility
from statConf import staticConfig

def __report_tax_issues(issues, verbose=1):
    print(f"\nERROR: Unable to determine taxonomy for {len(issues)} bins:")
    problematic_bins = [x['mag_bin'] for x in issues]
    problematic_bins = set(problematic_bins)
    for_printing = '\n'.join(problematic_bins)
    print(for_printing)
    print(f"Please manually enter taxonomy data for these bins into a .tsv file and specify it in the MANUAL_TAXONOMY_FILE field in the config file.")
    if verbose>0:
        print(f"\nTaxonomy issues are:")
        for i in issues:
            mag = i['mag_bin']
            level = i['level']
            classification = i['classification']
            suggestions = i['suggestions']
            if len(i['suggestions']) == 0:
                print(f"MAG {mag} - no suggestions found (classified as {level} {classification})")
            else:
                print(f"MAG {mag} - multiple suggestions found (classified as {level} {classification})")
                print("\tSuggestions are:")
                for s in suggestions:
                    print(f"\t{s['taxId']}\t{s['scientificName']}")
    exit(1)


def query_ena_taxonomy(level: str,
                         domain: str,
                         classification: str,
                         filtered: bool = True,
                         verbose: int = 1) -> list:
    """ Based on the query string, use the ENA REST API to get
        a suggestion for the taxonomy.
    """
    # If we know the species we just query for that.
    if level == 'species':
        query = classification
    # If we know the genus get a "<genus> sp." name
    elif level == 'genus':
        query = f"{classification} sp."
    # If we know only something higher then we get
    # "<classification> bacterium" / "<classification> archeon"
    else:
        if domain == 'Archaea':
            dstring = 'archaeon'
        elif domain == 'Bacteria':
            dstring = 'bacterium'
        elif domain == 'metagenome':
            dstring = 'metagenome'
        else:
            print(f"\nERROR: Encountered unknown domain {domain}")
            exit(1)
        if domain == 'metagenome':
            query = classification
        else:
            query = f"{classification} {dstring}"    
    
    url = f"https://www.ebi.ac.uk/ena/taxonomy/rest/suggest-for-submission/{query}"
    response = requests.get(url)
    if response.status_code == 200:
        suggestions = response.json()
        result = []
        for suggestion in suggestions:
            tax_id = suggestion.get("taxId", "N/A")
            scientific_name = suggestion.get("scientificName", "N/A")
            display_name = suggestion.get("displayName", "N/A")
            taxdata = {"tax_id": tax_id, "scientificName": scientific_name, "displayName": display_name}
            # If we don't filter we want all results
            if not filtered:
                result.append(taxdata)
            # For genus level we want the "is species of this genus" result
            elif level == 'genus':
                if scientific_name.endswith('sp.'):
                    result.append(taxdata)
            # For species, we want the result that is the species name (no subspecies)
            # It might have something like "Candidatus" in front so we don't exclude that
            elif level == 'species':
                if scientific_name.endswith(classification):
                    result.append(taxdata)
            # For all other cases we want the "<classification> <domain>" taxon.
            else:
                if scientific_name.endswith('archaeon') or scientific_name.endswith('bacterium') or level == 'metagenome':
                    result.append(taxdata)                  
        return result
    else:
        print(f"\nERROR: Trying to fetch taxonomy suggestion for {level}: {classification} (domain: {domain}) but ENA REST API returned status code {response.status_code}")
        if verbose > 0:
            print(f"Attempted query was {url}")
        exit(1)



def __calculate_bin_coverage(fasta: str,
                             depth_files: list,
                             threads=4,
                             verbose: int = 1) -> float:
    """
    Extract the names of contigs in the bin and calculate the bin coverage
    based on the depth files.

    Args:
        fasta (str): Path to the fasta file of the bin.
        depth_files (list): List of paths to the depth files.
        verbose (int, optional): Verbosity level. Defaults to 1.

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
    if verbose == 1:
        bin_verbosity = 0
    else:
        bin_verbosity = verbose
    coverage = utility.calculate_coverage(depth_files,
                                          contig_names,
                                          threads=threads,
                                          verbose=bin_verbosity)
    
    return coverage


def __read_ncbi_taxonomy(ncbi_taxonomy_file: str) -> dict:
    """
    Read the output of GTDB-TKs 'gtdb_to_ncbi_majority_vote.py' script and
    return a dictionary with a taxid and a scientific name for each genome.
    Important note: The output of GTDB-TKs 'gtdb_to_ncbi_majority_vote.py' script
    might miss some genome bins which didn't get GTDB classifications.
    """
    result = {}
    with open(ncbi_taxonomy_file, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader) #skip header
        for row in reader:
            mag_bin = row[0].strip()
            lowest_ncbi_name = row[2].strip().split(';')
            result[mag_bin] = lowest_ncbi_name
    return result


def __best_classifications(ncbi_classifications: dict) -> dict:
    """
    For each bin, find the best classification string. This is the classification
    string on the lowest level that is not empty.

    Args:
        ncbi_classifications (dict): A dictionary with a list of classification strings
        for each bin.

    Returns:
        dict: A dictionary with the best classification string for each bin.
    """
    result = {}
    levels = staticConfig.taxonomic_levels.split(';')
    for mag_bin, clist in ncbi_classifications.items():
        # Iterate through classification strings until we find a valid one
        for cstring, level in zip(reversed(clist), levels):
            if len(cstring) < 4: # no classification on this level
                continue
            break
        result[mag_bin] = {
            'level': level, 
            'classification': cstring[3:],
            'domain': clist[0][3:]
        }
    return result


def __taxonomic_classification(ncbi_taxonomy_files: list) -> dict:
    """
    Read the output of GTDB-TKs 'gtdb_to_ncbi_majority_vote.py' script and
    return a dictionary with a taxid and a scientific name for each genome.
    
    Args:
        ncbi_to_taxonomy_file (str): Output files of GTDB-TKs
        'gtdb_to_ncbi_majority_vote.py' script.

    Returns:
        dict: A dictionary with a taxid and a scientific name for each genome.
    """
    all_classifications = {}
    for f in ncbi_taxonomy_files:
        ncbi_classifications = __read_ncbi_taxonomy(f)
        best_ncbi_classifications = __best_classifications(ncbi_classifications)
        all_classifications.update(best_ncbi_classifications)
    return all_classifications


def __read_manual_taxonomy_file(manual_taxonomy_file: str,
                                verbose: int = 1) -> dict:
    """
    Read a manual taxonomy file and return a dictionary with the taxid and
    scientific name for each bin.
    """
    if verbose > 0:
        print(f">Reading manual taxonomy file {manual_taxonomy_file}")
    result = {}
    with open(manual_taxonomy_file, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader) #skip header
        for row in reader:
            mag_bin = row[0].strip()
            tax_id = row[2].strip()
            scientific_name = row[1].strip()
            result[mag_bin] = {
                'tax_id': tax_id,
                'scientific_name': scientific_name,
            }
    return result

def get_bin_taxonomy(config,
                     verbose=1) -> dict:

    # Extract data from config
    ncbi_taxonomy_files = utility.optional_from_config(config, 'BINS', 'NCBI_TAXONOMY_FILES')
    if ncbi_taxonomy_files == '': # Key not found in config
        ncbi_taxonomy_files = []
    if not type(ncbi_taxonomy_files) == list:
        ncbi_taxonomy_files = [ncbi_taxonomy_files]
    bins_directory = utility.from_config(config, 'BINS', 'BINS_DIRECTORY')

    # Make a list of all files in the bins directory
    files = os.listdir(bins_directory)
    bin_basenames = []
    for f in files:
        basename = utility.is_fasta(os.path.join(bins_directory, f))
        if basename:
            bin_basenames.append(basename)

    # Read the taxnomy data from the MANUAL_TAXONOMY_FILE if it exists
    upload_taxonomy_data = {}
    try:
        manual_taxonomy_file = utility.from_config(config,
                                                   'BINS',
                                                   'MANUAL_TAXONOMY_FILE',
                                                   supress_errors=True)
    except:
        manual_taxonomy_file = 'manual_taxonomy_file_doesnt_exist'
    if os.path.exists(manual_taxonomy_file):
        upload_taxonomy_data = __read_manual_taxonomy_file(manual_taxonomy_file, verbose)

    # Make a dictionary for the taxonomies based on the taxonomy files
    annotated_bin_taxonomies = __taxonomic_classification(ncbi_taxonomy_files)

    # Make sure that for each bin showing up in the taxonomy files we have a 
    # corresponding fasta file in bin_files
    from_taxonomies = set(upload_taxonomy_data.keys())
    from_taxonomies.update(set(annotated_bin_taxonomies.keys()))
    only_taxonomies = set(bin_basenames) - from_taxonomies
    if len(only_taxonomies) > 0:
        print(f"\nERROR: The following bins were found in the taxonomy files but not in the bins directory:")
        for b in only_taxonomies:
            print(f"\t{b}")
        exit(1)
    only_fasta = set(bin_basenames) - from_taxonomies
    if len(only_fasta) > 0:
        print(f"\nERROR: The following bins were found in the bins directory but not in the taxonomy files:")
        for b in only_fasta:
            print(f"\t{b}")
        exit(1)

    # Query the ENA API for taxids and scientific names for each bin
    if verbose > 0:
        print(">Querying ENA for taxids and scientific names for each bin.")
    issues = []
    for bin_name, taxonomy in tqdm(annotated_bin_taxonomies.items(), leave=False):
        if bin_name in upload_taxonomy_data:
            if verbose > 1:
                print(f"\t...skipping {bin_name} because it was found in the manual taxonomy file.")
            continue
        suggestions = query_ena_taxonomy(taxonomy['level'],
                                           taxonomy['domain'],
                                           taxonomy['classification'],
                                           filtered=True,
                                           verbose=verbose)
        if len(suggestions) == 1:
            upload_taxonomy_data[bin_name] = {
                'scientific_name': suggestions[0]['scientificName'],
                'tax_id': suggestions[0]['tax_id'],
            }
        else:
            all_ena_suggestions = query_ena_taxonomy(taxonomy['level'],
                                                       taxonomy['domain'],
                                                       taxonomy['classification'],
                                                       filtered=False,
                                                       verbose=verbose)
            issues.append({
                'mag_bin': bin_name,
                'level': taxonomy['level'],
                'classification': taxonomy['classification'],
                'suggestions': all_ena_suggestions,
            })

    # Add any bins that only show up in the files to the issues as unclassified
    for basename in bin_basenames:
        if not basename in upload_taxonomy_data:
            issues.append({
                'mag_bin': basename,
                'level': 'unclassified',
                'classification': 'unclassified',
                'suggestions': [],
            })

    if len(issues) > 0:
        __report_tax_issues(issues, verbose)
        exit(1)

    return upload_taxonomy_data

def get_bin_quality(config, verbose) -> dict:
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
    quality_file = utility.from_config(config, 'BINS', 'BINS_QUALITY_FILE')
    result = {}
    if verbose > 0:
        print(f"\t...reading bin quality file at {os.path.abspath(quality_file)}")
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
        print(f"\nERROR: The following bins were found in the quality file but not in the bins directory:")
        for b in only_in_quality:
            print(f"\t{b}")
        exit(1)
    only_in_directory = bin_basenames - set(result.keys())
    if len(only_in_directory) > 0:
        print(f"\nERROR: The following bins were found in the bins directory but not in the quality file:")
        for b in only_in_directory:
            print(f"\t{b}")
        exit(1)

    if verbose > 1:
        print(f"\t...found {len(result)} bins in bin quality file.")
    return result



def __prep_bins_samplesheet(config: dict,
                            samples_submission_dir: str,
                            upload_taxonomy_data: dict,
                            verbose: int = 1) -> str:
    """
    """
    if verbose > 0:
        print(f">Preparing bins samplesheet...")

    bin_quality = get_bin_quality(config, verbose=verbose)

#    project_name = utility.from_config(config, 'PROJECT_NAME')

    sequencing_platform = utility.from_config(config, 'ASSEMBLY', 'PLATFORM')
    if type(sequencing_platform) == list:
        sequencing_platform = ','.join(sequencing_platform)
    
    assembly_software = utility.from_config(config, 'ASSEMBLY', 'PROGRAM')
    
    completeness_software = utility.from_config(config, 'BINS', 'COMPLETENESS_SOFTWARE')
    
    binning_software = utility.from_config(config, 'BINS', 'BINNING_SOFTWARE')
    
    assembly_quality = staticConfig.bin_assembly_quality
    
#    isolation_source = utility.from_config(config, 'ASSEMBLY', 'ISOLATION_SOURCE')
    
    collection_date = utility.from_config(config, 'ASSEMBLY', 'DATE')
    
    geographic_location_country = utility.from_config(config, 'ASSEMBLY', 'LOCATION')
    
    #geographic_location_latitude = utility.optional_from_config(config, 'ASSEMBLY', 'LATITUDE')
    
    #geographic_location_longitude = utility.optional_from_config(config, 'ASSEMBLY', 'LONGITUDE')
    
    investigation_type = staticConfig.bin_investigation_type
    
    #binning_parameters = utility.from_config(config, 'BINS', 'BINNING_PARAMETERS')
    
    #taxonomic_identity_marker = utility.from_config(config, 'BINS', 'TAXONOMIC_IDENTITY_MARKER')
    
    #broad_env_context = utility.optional_from_config(config, 'ASSEMBLY', 'BROAD_ENVIRONMENTAL_CONTEXT')
    
    #local_env_context = utility.optional_from_config(config, 'ASSEMBLY', 'LOCAL_ENVIRONMENTAL_CONTEXT')
    
    #env_medium = utility.optional_from_config(config, 'ASSEMBLY', 'ENVIRONMENTAL_MEDIUM')
    
    sample_refs = utility.from_config(config, 'ASSEMBLY', 'SAMPLE_REFS')
    if type(sample_refs) == list:
        sample_refs = ','.join(sample_refs)
    sample_derived_from = sample_refs
    
    metagenomic_source = utility.from_config(config, 'ASSEMBLY', 'SPECIES_SCIENTIFIC_NAME')

    sequencing_method = utility.from_config(config, 'ASSEMBLY', 'PLATFORM')
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
        
        # Add all specified attributes
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
#            "binning parameters": binning_parameters,
#            "isolation_source": isolation_source,
            "collection date": collection_date,
            "geographic location (country and/or sea)": geographic_location_country,
#            "geographic location (latitude)": geographic_location_latitude,
#            "geographic location (longitude)": geographic_location_longitude,
#            "broad-scale environmental context": broad_env_context,
#            "local environmental context": local_env_context,
#            "environmental medium": env_medium,
            "sample derived from": sample_derived_from,
            "metagenomic source": metagenomic_source,
        }

        for key, value in attribute_data.items():
            if value:  # Only add attribute if value is not empty
                attribute = ET.SubElement(sample_attributes, "SAMPLE_ATTRIBUTE")
                ET.SubElement(attribute, "TAG").text = key
                ET.SubElement(attribute, "VALUE").text = value

    # Convert the XML structure to a string
    tree = ET.ElementTree(root)
    outpath = os.path.join(samples_submission_dir, "bins_samplesheet.xml")
    with open(outpath, 'wb') as f:
        tree.write(f, encoding='UTF-8', xml_declaration=False)

    if verbose > 0:
        print(f"\t...written bins samplesheet to {os.path.abspath(outpath)}")

    return outpath

def __read_bin_samples_receipt(receipt_path: str,
                               verbose: int = 1) -> dict:
    """
    """
    tree = ET.parse(receipt_path)
    root = tree.getroot()

    success = root.attrib['success']
    if success != 'true':
        print(f"\nERROR: Submission failed. Please consult the receipt file at {os.path.abspath(receipt_path)} for more information.")
        exit(1)

    if verbose>1:
        print("...bin samplesheet upload was successful.")


    bin_to_accession = {}
    for sample in root.findall('.//SAMPLE'):
        alias = sample.attrib.get('alias')
        if alias is None:
            print(f"\nERROR: Submission failed. Didn't find alias for all bins in the receipt. Please check the receipt at {os.path.abspath(receipt_path)}.")
            exit(1)
        ext_id = sample.find('EXT_ID')
        if ext_id is None:
            print(f"\nERROR: Submission failed. Didn't find EXT_ID for all bins in the receipt. Please check the receipt at {os.path.abspath(receipt_path)}.")
            exit(1)
        accession = ext_id.attrib.get('accession')
        bin_to_accession[alias] = accession

    return bin_to_accession

def __submit_bins_samplesheet(sample_xml: str,
                              staging_dir: str,
                              logging_dir: str,
                              url: str,
                              verbose: int = 1) -> str:
    """
    Uploads the samplesheet to ENA.

    Args:

    Returns:
        str: The accession number of the uploaded samplesheet.
    """

    # Make the submission xml
    submission_xml = os.path.join(staging_dir, 'bin_samplesheet_submission.xml')
    utility.build_sample_submission_xml(submission_xml,
                                        hold_until_date=None,
                                        verbose=verbose)
    
    receipt_path = os.path.join(logging_dir, "bins_samplesheet_receipt.xml")
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

    bin_to_accession = __read_bin_samples_receipt(receipt_path, verbose)

    return bin_to_accession


def __prep_bin_manifest(config: dict,
                        staging_directory: str,
                        bin_coverage: float,
                        bin_sample_accession: str,
                        gzipped_fasta_path: str,
                        verbose: int = 1) -> str:
    if verbose > 1:
        print(f"\t>Preparing bin manifest in {staging_directory}...")

    platform = utility.from_config(config, 'ASSEMBLY', 'PLATFORM')
    if isinstance(platform, list):
        platform = ",".join(platform)

    run_refs = utility.from_config(config, 'ASSEMBLY', 'RUN_REFS')
    if isinstance(run_refs, list):
        run_refs = ",".join(run_refs)

    bin_assembly_name = utility.from_config(config, 'ASSEMBLY', 'ASSEMBLY_NAME') + "_bin_" + bin_sample_accession
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
        ['PLATFORM', platform],
        ['MOLECULETYPE', utility.from_config(config, 'ASSEMBLY','MOLECULE_TYPE')],
    #    ['DESCRIPTION', utility.from_config(config, 'ASSEMBLY','DESCRIPTION')],
        ['RUN_REF', run_refs],
        ['FASTA', os.path.basename(gzipped_fasta_path)]
    ]

    manifest_path = os.path.join(staging_directory, "MANIFEST")
    with open(manifest_path, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    if verbose > 1:
        print(f"\t...written bin manifest to {os.path.abspath(manifest_path)}")

    return manifest_path

def __stage_bin_submission(staging_directory: str,
                           bin_name: str,
                           bin_fasta: str,
                           config: dict,
                           bin_sample_accession: str,
                           bin_coverage,
                           verbose: int = 1) -> None:
    """
    """
    
    # Stage the fasta file
    gzipped_fasta_path = os.path.join(staging_directory, "bin"+f"assembly_upload{staticConfig.zipped_fasta_extension}")
    if bin_fasta.endswith('.gz'):
        shutil.copyfile(bin_fasta, gzipped_fasta_path)
    else:
        with open(bin_fasta, 'rb') as f_in:
            with gzip.open(gzipped_fasta_path, 'wb') as f_out:
                f_out.writelines(f_in)

    # Make the MANIFEST file
    manifest_path = __prep_bin_manifest(config,
                                        staging_directory,
                                        bin_coverage,
                                        bin_sample_accession,
                                        gzipped_fasta_path,
                                        verbose=verbose)  

    return manifest_path          

    


def submit_bins(config: dict,
                upload_taxonomy_data: dict,
                staging_dir: str,
                logging_dir: str,
                depth_files: str,
                threads: int = 4,
                verbose: int = 1,
                test: bool = True,
                submit: bool = True) -> tuple:
    """
    """

    if test:
        url = staticConfig.ena_test_dropbox_url
    else:
        url = staticConfig.ena_dropbox_url
    
    # Extract data from config
    bins_directory = utility.from_config(config, 'BINS', 'BINS_DIRECTORY')

    # Make a list of all files in the bins directory and extract bin names
    bin_files = os.listdir(bins_directory)
    bin_name_to_fasta = {}
    for f in bin_files:
        bin_name = utility.is_fasta(os.path.join(bins_directory, f))
        if bin_name is None:
            if verbose > 0:
                print(f"\t...skipping {f} because it does not seem to be a fasta file.")
            continue
        bin_name_to_fasta[bin_name] = os.path.join(bins_directory, f)

    # Get the coverage for each bin file
    if verbose > 0:
        print(">Calculating coverage for each bin.")
    bin_coverages = {}
    for f in tqdm(bin_files, leave=False):
        bin_file = os.path.join(bins_directory, f)
        bin_name = f.split('.')[:-1]
        assert len(bin_name) == 1
        bin_name = bin_name[0]
        coverage = __calculate_bin_coverage(bin_file,
                                            depth_files,
                                            threads=threads,
                                            verbose=verbose)
        bin_coverages[bin_name] = coverage

    # Make a samplesheet for all bins
    samples_submission_dir = os.path.join(staging_dir, 'bin_samplesheet')
    os.makedirs(samples_submission_dir, exist_ok=False)
    samplesheet = __prep_bins_samplesheet(config,
                                          samples_submission_dir,
                                          upload_taxonomy_data,
                                          verbose)
    
    # Upload the samplesheet
    samples_logging_dir = os.path.join(logging_dir, 'bin_samplesheet')
    os.makedirs(samples_logging_dir, exist_ok=False)
    prefixbin_to_accession = __submit_bins_samplesheet(samplesheet,
                                                    samples_submission_dir,
                                                    samples_logging_dir,
                                                    url,
                                                    verbose)
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
    if verbose > 0:
        print(f">Staging bin submission sequences and manifests...")
    bin_manifests = {}
    for bin_name, bin_fasta in bin_name_to_fasta.items():
        bin_sample_accession = bin_to_accession[bin_name]
        staging_directory = os.path.join(staging_dir, f"bin_{bin_name}_staging")
        staging_directories[bin_name] = staging_directory
        os.makedirs(staging_directory, exist_ok=False)
        
        bin_manifests[bin_name] = __stage_bin_submission(staging_directory,
                                                         bin_name,
                                                         bin_fasta,
                                                         config,
                                                         bin_sample_accession,
                                                         bin_coverages[bin_name],
                                                         verbose)


    # Upload the bins
    if verbose>0:
        print(f">Using ENA webin-cli to submit bins.\n")
    usr, pwd = utility.get_login()
    bin_receipts = {}
    bin_accessions = {}
    for bin_name, bin_staging_dir in staging_directories.items():
        bin_logging_dir = os.path.join(logging_dir, f"{bin_name}")
        os.makedirs(bin_logging_dir, exist_ok=False)
        bin_manifest = bin_manifests[bin_name]
        bin_staging_dir = staging_directories[bin_name]
        assembly_name = utility.from_config(config, 'ASSEMBLY','ASSEMBLY_NAME')
        subdir_name = assembly_name + '_' + bin_name

        bin_receipts[bin_name], bin_accessions[bin_name] = webin_cli(manifest=bin_manifest,
                                                                     inputdir=bin_staging_dir,
                                                                     outputdir=bin_logging_dir,
                                                                     username=usr,
                                                                     password=pwd,
                                                                     subdir_name=subdir_name,
                                                                     submit=submit,
                                                                     test=test,
                                                                     verbose=verbose)
        print("")
        
    if verbose>0:
        print("\n>Bin submission completed!")
    if verbose>1:
        print(f">Bin receipt paths are:")
        for bin_name, bin_receipt in bin_receipts.items():
            print(f"\t{bin_name}: {bin_receipt}")

    bin_to_accession_file = os.path.join(logging_dir, 'bin_to_preliminary_accession.tsv')
    with open(bin_to_accession_file, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for bin_name, accession in bin_accessions.items():
            writer.writerow([bin_name, accession])

    print(f">The preliminary(!) accessions of your bins have been written to {bin_to_accession_file}.")