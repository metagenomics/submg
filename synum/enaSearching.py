#from synum import utility

#from synum.statConf import staticConfig

import requests


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


def search_samples_by_assembly_analysis(assembly_analysis_accession):
    """
    Get a list of sample accessions for a given assembly analysis accession.
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
        print(f"\nERROR: Multiple sample accessions found for assembly analysis {assembly_analysis_accession}:\n{sample_accession}")
        exit(1)

    return sample_accession



#print(search_samples_by_assembly_analysis('ERZ1049590'))
#print(search_runs_by_sample('SAMEA113417025'))