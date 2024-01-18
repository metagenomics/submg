#from synum import utility

#from synum.statConf import staticConfig

import requests


def search_runs_by_sample(sample_accession):
    """
    Get a list of run accessions for a given sample accession.
    """
    url = "https://www.ebi.ac.uk/ena/portal/api/search"
    #url = staticConfig.ena_search_url
    params = {
        "query": f"sample_accession={sample_accession}",
        "result": "read_run",
        "fields": "run_accession"
    }
    response = requests.get(url, params=params)
    #utility.api_response_check(response)

    #print(response.url)  # This will show you the full URL after adding the parameters
    #print(response.status_code)
    run_accessions = response.text.split('\n')[1:-1]

    return run_accessions
    print(fields)
    print(response.text.split('\n'))

    print(type(response.text))
print(search_runs_by_sample('SAMEA113417025'))