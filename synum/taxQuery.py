import os
import csv
import requests
import time

from tqdm import tqdm
from synum import utility, loggingC
from synum.statConf import staticConfig


def __report_tax_issues(issues):
    """
    When the tool fails because of issues with trying to determine the taxonomy
    of metagenome bins automatically, this function reports the issues in
    detail before exiting the program.

    Args:
        issues (list): A list of dictionaries with the issues encountered.
    """
    # Log the error
    err = f"\nERROR: Unable to determine taxonomy for {len(issues)} bins:"
    loggingC.message(err, threshold=-1)
    problematic_bins = [x['mag_bin'] for x in issues]
    problematic_bins = set(problematic_bins)
    msg = '\n'.join(problematic_bins)
    loggingC.message(msg, threshold=-1)
    msg = "Please consult the README. You can manually enter taxonomy data for these bins into a .tsv file and specify it in the MANUAL_TAXONOMY_FILE field in the config file."
    loggingC.message(msg, threshold=-1) 

    # Give a detailed listing of the issues
    msg = f"\nTaxonomy issues are:"
    loggingC.message(msg, threshold=0)
    for i in issues:
        mag = i['mag_bin']
        level = i['level']
        classification = i['classification']
        suggestions = i['suggestions']
        if len(i['suggestions']) == 0:
            if classification == 'N/A':
                msg = f"bin/MAG {mag} - was not present in any NCBI_TAXONOMY_FILES or MANUAL_TAXONOMY_FILE" 
            else:
                msg = f"bin/MAG {mag} - no suggestions found (classified as {level} {classification})"
            loggingC.message(msg, threshold=0)
        else:
            loggingC.message(f"bin/MAG {mag} - multiple suggestions found (classified as {level} {classification})", threshold=0)
            loggingC.message("\tSuggestions are:", threshold=0)
            for s in suggestions:
                loggingC.message(f"\t{s['taxId']}\t{s['scientificName']}", threshold=0)
    
    exit(1)


def __check_bin_coherence(bin_basenames: list,
                          annotated_bin_taxonomies: dict,
                          upload_taxonomy_data: dict):
    """
    Check if the bins in the BINS_DIRECTORY are consistent with the taxonomy
    files. If a bin is in the BINS_DIRECTORY but not in the taxonomy files, or
    vice versa, the program will exit with an error message.

    Args:
        bin_basenames (list): A list of the basenames of the bins in the
            BINS_DIRECTORY
        annotated_bin_taxonomies (dict): A dictionary with the taxid and
            scientific name for each bin in the taxonomy files
        upload_taxonomy_data (dict): A dictionary with the taxid and scientific
            name for each bin in the manual taxonomy file
    """
    ids_from_taxonomies = set(upload_taxonomy_data.keys())
    ids_from_taxonomies.update(set(annotated_bin_taxonomies.keys()))
    ids_from_fasta = set(bin_basenames)

    only_in_fasta = ids_from_fasta.difference(ids_from_taxonomies)
    only_in_taxonomies = ids_from_taxonomies.difference(ids_from_fasta)

    if len(only_in_fasta) > 0:
        err = f"\nERROR: The following bins are in the BINS_DIRECTORY but not in the taxonomy files:"
        loggingC.message(err, threshold=-1)
        for b in only_in_fasta:
            msg = f"\t{b}"
            loggingC.message(msg, threshold=0)
        exit(1)
    if len(only_in_taxonomies) > 0:
        err = f"\nERROR: The following bins are in the taxonomy files but not in the BINS_DIRECTORY:"
        loggingC.message(err, threshold=-1)
        for b in only_in_taxonomies:
            msg = f"\t{b}"
            loggingC.message(msg, threshold=0)
        exit(1)


def __read_manual_taxonomy_file(manual_taxonomy_file: str) -> dict:
    """
    Read a manual taxonomy file and return a dictionary with the taxid and
    scientific name for each bin.

    Args:
        manual_taxonomy_file (str): Path to the manual taxonomy file.

    Returns:
        dict: A dictionary with the taxid and scientific name for each bin.
    """
    result = {}
    with open(manual_taxonomy_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            mag_bin = row['Bin_id'].strip()
            tax_id = row['Tax_id'].strip()
            scientific_name = row["Scientific_name"].strip()
            result[mag_bin] = {
                'tax_id': tax_id,
                'scientific_name': scientific_name,
            }
    return result


def __read_ncbi_taxonomy(ncbi_taxonomy_file: str) -> dict:
    """
    Read the output of GTDB-TKs 'gtdb_to_ncbi_majority_vote.py' or a file using
    the format described in README.md and return a dictionary with a taxid and a
    scientific name for each genome.
    Important note: The output of GTDB-TKs 'gtdb_to_ncbi_majority_vote.py' script
    might miss some genome bins which didn't get GTDB classifications.

    Args:
        ncbi_to_taxonomy_file (str): Output files of GTDB-TKs
            'gtdb_to_ncbi_majority_vote.py' script or NCBI taxonomy file with a
            the columns 'Bin_id' and 'NCBI_taxonomy'.

    Returns:
        dict: A dictionary with a taxid and a scientific name for each genome. 
    """
    result = {}
    with open(ncbi_taxonomy_file, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader) #skip header
        if header == staticConfig.gtdb_majority_vote_columns.split(';'):
            gtdb_majvote_output = True
        else:
            gtdb_majvote_output = False
    if gtdb_majvote_output:
        with open(ncbi_taxonomy_file, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader) #skip header
            for row in reader:
                mag_bin = row[0].strip()
                lowest_ncbi_name = row[2].strip().split(';')
                result[mag_bin] = lowest_ncbi_name
    else:
        with open(ncbi_taxonomy_file, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                mag_bin = row["Bin_id"].strip()
                taxonomy_string = row["NCBI_taxonomy"].strip()
                lowest_ncbi_name = taxonomy_string.split(';')
                result[mag_bin] = lowest_ncbi_name
    return result


def __best_classification(ncbi_classifications: dict) -> dict:
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
        # Check if we have an "unclassified" bin here
        if len(clist) == 1:
            clasf = clist[0]
            if clasf == 'Unclassified Bacteria':
                result[mag_bin] = {
                    'level': 'domain',
                    'classification': 'Bacteria',
                    'domain': 'Bacteria',
                }
            elif clasf.startswith('Unclassified Eukaryot'):
                result[mag_bin] = {
                    'level': 'domain',
                    'classification': 'Eukaryota',
                    'domain': 'Eukaryota',
                }
            elif clasf == 'Unclassified Archaea':
                result[mag_bin] = {
                    'level': 'domain',
                    'classification': 'Archaea',
                    'domain': 'Archaea',
                }
            else:
                err = f"\nERROR: Found unclassified bin {mag_bin} with unknown classification {clasf}. Please check your NCBI taxonomy files."
                loggingC.message(err, threshold=-1)
                exit(1)
            loggingC.message(f">INFO: Bin {mag_bin} is unclassified.", threshold=1)
        else:
            # Iterate through classification strings until we find a valid one
            for cstring, level in zip(reversed(clist), levels):
                if len(cstring) < 4: # no classification on this level
                    continue
                break
            # If this is unclassified we need to include some padding
            if cstring.startswith('Unclassified'):
                cstring = '___'+cstring
                clist[0] = '___'+clist[0]
            result[mag_bin] = {
                'level': level, 
                'classification': cstring[3:],
                'domain': clist[0][3:]
            }
    return result


def ena_taxonomy_suggestion(level: str,
                            domain: str,
                            classification: str,
                            filtered: bool = True) -> list:
    """ 
    Based on the query string, use the ENA REST API to get a suggestion for the
    taxonomy. An exception for deltaproteobacteria family doesn't seem to be
    necessary when using the suggest_for_submission API.

    Args:
        level (str): The taxonomic level of the query string.
        domain (str): The domain of the query string.
        classification (str): The query string.
        filtered (bool, optional): If True, only return the best suggestion.
            Defaults to True.

    Returns:
        list: A list of dictionaries with the suggestions from the ENA REST API.
    """
    # If we know the species we just query for that.
    if level == 'species':
        query = classification
    # If we know the genus get a "<genus> sp." name
    elif level == 'genus':
        query = f"{classification} sp."
    # If we only know the domain, we get "<uncultured> domain"
    elif level == 'domain':
        if domain == 'Archaea':
            query = 'uncultured archaeon'
        elif domain == 'Bacteria':
            query = 'uncultured bacterium'
        elif domain == 'Eukaryota':
            query = 'uncultured eukaryote'
        else:
            err = f"\nERROR: Encountered unknown domain {domain} for a mag bin. Please check your NCBI taxonomy files."
            loggingC.message(err, threshold=-1)
            exit(1)
    # If we know only something between domain and genus then we get
    # "<classification> bacterium" / "<classification> archeon"
    else:
        if domain == 'Archaea':
            dstring = 'archaeon'
        elif domain == 'Bacteria':
            dstring = 'bacterium'
        elif domain == 'Eukaryota':
            dstring = 'eukaryote'
        elif domain == 'metagenome':
            dstring = 'metagenome'
        else:
            err = f"\nERROR: Encountered unknown domain {domain}"
            loggingC.message(err, threshold=-1)
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
                if scientific_name.endswith('archaeon') or scientific_name.endswith('bacterium') or scientific_name.endswith('eukaryote') or level == 'metagenome':
                    result.append(taxdata)                  
        return result
    else:
        err = f"\nERROR: Trying to fetch taxonomy suggestion for {level}: {classification} (domain: {domain}) but ENA REST API returned status code {response.status_code}"
        loggingC.message(err, threshold=-1)
        loggingC.message(f"Attempted query was {url}", threshold=0)
        exit(1)


def __parse_classification_tsvs(ncbi_taxonomy_files: list) -> dict:
    """
    Read the output of GTDB-TKs 'gtdb_to_ncbi_majority_vote.py' script or a file
    using the format described in README.md and return a dictionary with a taxid
    and a scientific name for each genome.
    
    Args:
        ncbi_to_taxonomy_file (str): Output files of GTDB-TKs
            'gtdb_to_ncbi_majority_vote.py' script or NCBI taxonomy file with a
            similar structure.

    Returns:
        dict: A dictionary with a taxid and a scientific name for each genome.
    """
    all_classifications = {}
    for f in ncbi_taxonomy_files:
        ncbi_classifications = __read_ncbi_taxonomy(f)
        best_ncbi_classification = __best_classification(ncbi_classifications)
        all_classifications.update(best_ncbi_classification)
    return all_classifications


def get_bin_taxonomy(config) -> dict:
    """
    Based on the NCBI taxonomy files and manual taxonomy file defined in the
    config, derive the taxid and scientific name for each bin

    Args:
        config (dict): The configuration dictionary

    Returns:
        dict: The dictionary with 'tax_id' and 'scientific_name' for each Bin_id
    """
    loggingC.message(">Reading in bin taxonomy data", threshold=0)

    # Make a list of all files in the bins directory
    bins_directory = utility.from_config(config, 'BINS', 'BINS_DIRECTORY')
    files = os.listdir(bins_directory)
    bin_basenames = []
    for f in files:
        basename = utility.is_fasta(os.path.join(bins_directory, f))
        if basename:
            bin_basenames.append(basename)

    # Get taxonomies from MANUAL_TAXONOMY_FILE if it exists
    upload_taxonomy_data = {}
    try:
        manual_taxonomy_file = utility.from_config(config,
                                                   'BINS',
                                                   'MANUAL_TAXONOMY_FILE',
                                                   supress_errors=True)
        loggingC.message(f">Reading manual taxonomy file {os.path.basename(manual_taxonomy_file)}", threshold=0)
    except:
        manual_taxonomy_file = 'manual_taxonomy_file_doesnt_exist'
        loggingC.message(">No manual taxonomy file found.", threshold=0)
    if os.path.exists(manual_taxonomy_file):
        if not manual_taxonomy_file == 'manual_taxonomy_file_doesnt_exist':
            upload_taxonomy_data = __read_manual_taxonomy_file(manual_taxonomy_file)


    # Read data from NCBI_TAXONOMY_FILES
    ncbi_taxonomy_files = utility.optional_from_config(config, 'BINS', 'NCBI_TAXONOMY_FILES')
    if ncbi_taxonomy_files == '': # Key not found in config
        ncbi_taxonomy_files = []
        loggingC.message(">No NCBI taxonomy files found in config.", threshold=0)
    if not type(ncbi_taxonomy_files) == list:
        ncbi_taxonomy_files = [ncbi_taxonomy_files]

    # Derive tax_id and scientific_name for each bin in NCBI_TAXONOMY_FILES
    annotated_bin_taxonomies = __parse_classification_tsvs(ncbi_taxonomy_files)

    # Make sure that, for each bin showing up in the taxonomy files, we have
    # a corresponding fasta file
    __check_bin_coherence(bin_basenames,
                          annotated_bin_taxonomies,
                          upload_taxonomy_data)
    

    # Query the ENA API for taxids and scientific names for each bin
    loggingC.message(">Querying ENA for taxids and scientific names for each bin.", threshold=0)

    issues = []
    min_interval = 1.0 / staticConfig.ena_rest_rate_limit
    last_request_time = time.time() - min_interval

    for bin_name, taxonomy in tqdm(annotated_bin_taxonomies.items(), leave=False):
        # Make sure we don't run into the ENA API rate limit
        current_time = time.time()
        time_since_last_request = current_time - last_request_time
        if time_since_last_request < min_interval:
            time.sleep(min_interval - time_since_last_request)
        last_request_time = time.time()

        # Get Taxonomy
        if bin_name in upload_taxonomy_data:
            loggingC.message(f">INFO: Bin {bin_name} was found in the manual taxonomy file and will be skipped.", threshold=1)
            continue
        suggestions = ena_taxonomy_suggestion(taxonomy['level'],
                                              taxonomy['domain'],
                                              taxonomy['classification'],
                                              filtered=True)
        if len(suggestions) == 1:
            upload_taxonomy_data[bin_name] = {
                'scientific_name': suggestions[0]['scientificName'],
                'tax_id': suggestions[0]['tax_id'],
            }
        else:
            all_ena_suggestions = ena_taxonomy_suggestion(taxonomy['level'],
                                                          taxonomy['domain'],
                                                          taxonomy['classification'],
                                                          filtered=False)

            issues.append({
                'mag_bin': bin_name,
                'level': taxonomy['level'],
                'classification': taxonomy['classification'],
                'suggestions': all_ena_suggestions,
            })

    # Add any bins that only show up in the files to the issues as unclassified
    for basename in bin_basenames:
        if not basename in upload_taxonomy_data:
            is_issue = False
            for i in issues:
                if i['mag_bin'] == basename:
                    is_issue = True
            if is_issue:
                continue
            issues.append({
                'mag_bin': basename,
                'level': 'unclassified',
                'classification': 'N/A',
                'suggestions': [],
            })

    if len(issues) > 0:
        __report_tax_issues(issues)
        exit(1)

    return upload_taxonomy_data


def taxid_from_scientific_name(scientific_name: str) -> str:
    """
    Get the taxid for a given scientific name from the ENA API. Returns None
    if no taxid is found.

    Args:
        scientific_name (str): The scientific name to query for.
    """
    url = f"https://www.ebi.ac.uk/ena/taxonomy/rest/scientific-name/{scientific_name}"
    response = requests.get(url)
    items = response.json()
    if not (len(items) == 1):
        return None
    if not (scientific_name == items[0]['scientificName']):
        return None
    tax_id = items[0]['taxId']
    return tax_id
