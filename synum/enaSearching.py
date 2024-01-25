#from synum import utility

#from synum.statConf import staticConfig

import requests

from synum import loggingC

def search_samples_by_assembly_analysis(assembly_analysis_accession):
    """
    Get a list of sample accessions for a given assembly analysis accession.

    Args:
        assembly_analysis_accession (str): The assembly analysis accession.

    Returns:
        str: A single sample accession.
    """
    url = "https://www.ebi.ac.uk/ena/portal/api/search"
    #url = staticConfig.ena_search_url
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

def search_scientific_name_by_sample(sample_accession):
    """
    Get the scientific name for a given sample accession.

    Args:
        sample_accession (str): A sample accession.

    Returns:
        str: The scientific name of the sample.
    """
    url = "https://www.ebi.ac.uk/ena/portal/api/search"
    #url = staticConfig.ena_search_url
    params = {
        "query": f"sample_accession={sample_accession}",
        "result": "sample",
        "fields": "scientific_name"
    }
    response = requests.get(url, params=params)

    scientific_name = response.text.split('\n')[1:-1][0]
    scientific_name = scientific_name.split('\t')[0]

    if ',' in scientific_name:
        loggingC.message(f"\nERROR: Multiple scientific names found for sample {sample_accession}:\n{scientific_name}", threshold=-1)
        exit(1)

    return scientific_name

#For debugging
#print(search_scientific_name_by_sample("SAMEA114749859"))
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