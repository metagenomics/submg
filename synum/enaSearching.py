import requests

#from synum import utility
from synum import loggingC
from synum.statConf import staticConfig


def study_exists(study_accession: str,
                 testmode: bool) -> bool:
    """
    Check if a study with the input accession exists in ENA.

    Args:
        study_accession (str): The study accession.
        testmode (bool):       Whether to use the test server.

    Returns:
        bool: True if the study exists, False if not.
    """
    if testmode:
        #url = "https://wwwdev.ebi.ac.uk/ena/portal/api/search"
        url = staticConfig.ena_search_url
    else:
        #url = "https://www.ebi.ac.uk/ena/portal/api/search"
        url = staticConfig.ena_test_search_url
    params = {
        "query": f"study_accession={study_accession}",
        "result": "study",
        "fields": "study_accession"
    }
    response = requests.get(url, params=params)
    
    data = response.text.split('\n')
    if (data[0] != 'study_accession') or (data[1] not in [study_accession, '']):
        loggingC.message(f"\nERROR: Unexpected response when querying ENA API for study accession {study_accession}.", threshold=-1)
        exit(1)
    if data[1] == study_accession:
        return True
    return False


def sample_exists(sample_accession: str,
                  testmode: bool) -> bool:
    """
    """
    if testmode:
        #url = "https://wwwdev.ebi.ac.uk/ena/portal/api/search"
        url = staticConfig.ena_search_url
    else:
        #url = "https://www.ebi.ac.uk/ena/portal/api/search"
        url = staticConfig.ena_test_search_url
    params = {
        "query": f"sample_accession={sample_accession}",
        "result": "sample",
        "fields": "sample_accession"
    }
    response = requests.get(url, params=params)

    data = response.text.split('\n')
    if (data[0] != 'sample_accession') or (data[1] not in [sample_accession, '']):
        loggingC.message(f"\nERROR: Unexpected response when querying ENA API for sample accession {sample_accession}.", threshold=-1)
        exit(1)
    if data[1] == sample_accession:
        return True
    return False


def search_samples_by_assembly_analysis(assembly_analysis_accession: str,
                                        testmode: bool) -> list:
    """
    Get a list of sample accessions for a given assembly analysis accession.

    Args:
        assembly_analysis_accession (str): The assembly analysis accession.

    Returns:
        str: A single sample accession.
    """
    if testmode:
        #url = "https://wwwdev.ebi.ac.uk/ena/portal/api/search"
        url = staticConfig.ena_search_url
    else:
        #url = "https://www.ebi.ac.uk/ena/portal/api/search"
        url = staticConfig.ena_test_search_url
    params = {
        "query": f"analysis_accession={assembly_analysis_accession}",
        "result": "analysis",
        "fields": "sample_accession"
    }
    response = requests.get(url, params=params)

    sample_accession = response.text.split('\n')[1:-1][0]
    sample_accession = sample_accession.split('\t')[0]

    if ',' in sample_accession:
        loggingC.message(f"\nERROR: Multiple sample accessions found for assembly analysis {assembly_analysis_accession}:\n{sample_accession}", threshold=-1)
        exit(1)

    return sample_accession


def search_scientific_name_by_sample(sample_accession: str,
                                     testmode: bool) -> str:
    """
    Get the scientific name for a given sample accession.

    Args:
        sample_accession (str): A sample accession.

    Returns:
        str: The scientific name of the sample.
    """
    print("CALLED WITH")
    print(sample_accession)
    print(testmode)
    print("-----------------------------------")
    if testmode:
        #url = "https://wwwdev.ebi.ac.uk/ena/portal/api/search"
        url = staticConfig.ena_search_url
    else:
        #url = "https://www.ebi.ac.uk/ena/portal/api/search"
        url = staticConfig.ena_test_search_url
    params = {
        "query": f"sample_accession={sample_accession}",
        "result": "sample",
        "fields": "scientific_name"
    }
    response = requests.get(url, params=params)
    print(response.text)

    try:
        scientific_name = response.text.split('\n')[1:-1][0]
        scientific_name = scientific_name.split('\t')[0]
    except IndexError:
        loggingC.message(f"\nERROR: No scientific name found for {sample_accession}. After submission, it can take some hours before an accession can be found through the ENA search. Please check if you can find this accession using the search function of the web interface.", threshold=-1)
        exit(1)

    if ',' in scientific_name:
        loggingC.message(f"\nERROR: Multiple scientific names found for sample {sample_accession}:\n{scientific_name}", threshold=-1)
        exit(1)

    return scientific_name

#For debugging
#print(sample_exists('SAMEA113417025', True))
#print(study_exists("PRJEB71644", True))

#print(search_scientific_name_by_sample('ERS28140038', True))
#print(search_scientific_name_by_sample("SAMEA114749859", True))
#print(search_samples_by_assembly_analysis('ERZ1049590'))
#print(search_runs_by_sample('SAMEA113417025'))

# def search_runs_by_sample(sample_accession):
#     """
#     Get a list of run accessions for a given sample accession.
#     """
#     url = "https://www.ebi.ac.uk/ena/portal/api/search"
#     #url = staticConfig.ena_search_url
#     params = {
#         "query": f"sample_accession={sample_accession}",
#         "result": "read_run",
#         "fields": "run_accession"
#     }
#     response = requests.get(url, params=params)
#     #utility.api_response_check(response)

#     #print(response.url)  # This will show you the full URL after adding the parameters
#     #print(response.status_code)
#     run_accessions = response.text.split('\n')[1:-1]
#     print(response.text.split('\n'))

#     print(type(response.text))
#     print((run_accessions))
#     return run_accessions