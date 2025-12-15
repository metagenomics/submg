import requests
import sys
from requests.exceptions import ConnectionError, ConnectTimeout, HTTPError, RequestException


from submg.modules import loggingC
from submg.modules.statConf import staticConfig



def ensure_server_online(url: str, timeout: float = 5.0):
    """
    Check that the server at `url` is reachable and free of server-side failures.

    Attempts an HTTP OPTIONS request to determine reachability. Handles:
      - ConnectTimeout: no response in time (client-side timeout).
      - ConnectionError: unable to establish a TCP connection (server offline).
      - HTTPError with status >= 500: server-side errors.
    Treats 4xx responses as “reachable but client-side issues” and does not exit.
    """
    try:
        # Use OPTIONS since some APIs reject HEAD without params
        resp = requests.options(url, timeout=timeout)
        resp.raise_for_status()
    except ConnectTimeout as e:
        loggingC.message(
            f"ERROR: Connection to {url} timed out.\n\t[{e}]",
            threshold=-1
        )
        sys.exit(1)
    except ConnectionError as e:
        loggingC.message(
            f"ERROR: Cannot connect to {url} (server offline?).\n\t[{e}]",
            threshold=-1
        )
        sys.exit(1)
    except HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        if status and status >= 500:
            loggingC.message(
                f"ERROR: Server error at {url} (status code {status}).\n\t[{e}]",
                threshold=-1
            )
            sys.exit(1)
    except RequestException:
        # Other errors (e.g., TooManyRedirects); propagate or handle as needed
        raise


def study_exists(study_accession: str,
                 devserver: bool = False) -> bool:
    """
    Check if a study with the input accession exists in ENA.

    Args:
        study_accession (str): The study accession.
        devserver (bool):       Whether to use the test server.

    Returns:
        bool: True if the study exists, False if not.
    """
    if devserver:
        url = staticConfig.ena_test_search_url
    else:
        url = staticConfig.ena_search_url
    ensure_server_online(url)
    
    params = {
        "query": f"study_accession={study_accession}",
        "result": "study",
        "fields": "study_accession"
    }
    response = requests.get(url, params=params)

    data = response.text.split('\n')
    if (data[0] != 'study_accession') or (data[1] not in [study_accession, '']):
        # There are some weird issues when querying the development server API
        # So if the query fails we try to find the study on the production
        # server. This _might_ lead to issues when the study is not yet
        # available on dev.
        if devserver:
            return study_exists(study_accession, False)
        loggingC.message(f"\nERROR: Unexpected response when querying ENA API for study accession {study_accession}.", threshold=-1)
        sys.exit(1)
    if data[1] == study_accession:
        return True
    return False


def sample_accession_exists(sample_accession: str,  
                            devserver: bool = False) -> bool:
    """
    Check if a sample with the input accession exists in ENA.

    Args:
        sample_accession (str): The sample accession.
        devserver (bool):        Whether to use the test server.

    Returns:
        bool: True if the sample exists, False if not.
    """
    if devserver:
        url = staticConfig.ena_test_search_url
    else:
        url = staticConfig.ena_search_url
    ensure_server_online(url)

    params = {
        "query": f"sample_accession={sample_accession}",
        "result": "sample",
        "fields": "sample_accession"
    }
    response = requests.get(url, params=params)

    data = response.text.split('\n')
    if (data[0] != 'sample_accession') or (data[1] not in [sample_accession, '']):
        loggingC.message(f"\nERROR: Unexpected response when querying ENA API for sample accession {sample_accession}.", threshold=-1)
        sys.exit(1)
    if data[1] == sample_accession:
        return True
    return False


def sample_alias_accession(sample_alias: str,
                           study_accession: str,
                           devserver: bool) -> bool:
    """
    Check if a sample with the input alias exists in ENA. Return the accession
    if it does or None if it does not.

    Args:
        sample_alias (str):     The sample alias.
        study_accession (str):  The study accession.
        devserver (bool):        Whether to use the test server.
    """
    if devserver:
        url = staticConfig.ena_test_search_url
    else:
        url = staticConfig.ena_search_url
    ensure_server_online(url)

    params = {
        "query": f"sample_alias={sample_alias} AND study_accession={study_accession}",
        "result": "sample",
        "fields": "sample_accession"
    }
    response = requests.get(url, params=params)
    try:
        data = response.text.split('\n')[1]
    except:
        data = None
    if data == '':
        data = None
    return data


def sample_title_accession(sample_title: str,
                           study_accession: str,
                           devserver: bool) -> bool:
    """
    Check if a sample with the input title exists in ENA. Return the accession
    if it does or None if it does not.

    Args:
        sample_title (str):     The sample title.
        study_accession (str):  The study accession.
        devserver (bool):        Whether to use the test server.
    """
    if devserver:
        url = staticConfig.ena_test_search_url
    else:
        url = staticConfig.ena_search_url
    ensure_server_online(url)

    params = {
        "query": f"sample_title={sample_title} AND study_accession={study_accession}",
        "result": "sample",
        "fields": "sample_accession"
    }
    response = requests.get(url, params=params)
    try:
        data = response.text.split('\n')[1]
    except:
        data = None
    if data == '':
        data = None
    return data



def run_alias_accession(run_alias: str,
                        study_accession: str,
                        devserver: bool) -> bool:
    """
    Check if a run with the input name exists in ENA. Return the accession
    if it does or None if it does not.

    Args:
        run_alias (str):        The run name.
        study_accession (str):  The study accession.
        devserver (bool):        Whether to use the test server.
    """
    if devserver:
        url = staticConfig.ena_test_search_url
    else:
        url = staticConfig.ena_search_url
    ensure_server_online(url)

    params = {
        "query": f"run_alias={run_alias} AND study_accession={study_accession}",
        "result": "read_run",
        "fields": "run_accession"
    }
    response = requests.get(url, params=params)
    try:
        data = response.text.split('\n')[1]
    except:
        data = None
    if data == '':
        data = None
    return data


def search_samples_by_assembly_analysis(assembly_analysis_accession: str,
                                        devserver: bool) -> list:
    """
    Get a list of sample accessions for a given assembly analysis accession.

    Args:
        assembly_analysis_accession (str): The assembly analysis accession.

    Returns:
        str: A single sample accession.
    """
    if devserver:
        url = staticConfig.ena_test_search_url
    else:
        url = staticConfig.ena_search_url
    ensure_server_online(url)

    params = {
        "query": f"analysis_accession={assembly_analysis_accession}",
        "result": "analysis",
        "fields": "sample_accession"
    }
    response = requests.get(url, params=params)

    try:
        sample_accession = response.text.split('\n')[1:-1][0]
        sample_accession = sample_accession.split('\t')[0]
    except:
        return None

    if ',' in sample_accession:
        loggingC.message(f"\nERROR: Multiple sample accessions found for assembly analysis {assembly_analysis_accession}:\n{sample_accession}", threshold=-1)
        sys.exit(1)

    return sample_accession


def search_scientific_name_by_sample(sample_accession: str,
                                     devserver: bool) -> str:
    """
    Get the scientific name for a given sample accession.

    Args:
        sample_accession (str): A sample accession.

    Returns:
        str: The scientific name of the sample.
    """
    if devserver:
        url = staticConfig.ena_test_search_url
    else:
        url = staticConfig.ena_search_url
    ensure_server_online(url)

    params = {
        "query": f"sample_accession={sample_accession}",
        "result": "sample",
        "fields": "scientific_name"
    }
    response = requests.get(url, params=params)
    try:
        scientific_name = response.text.split('\n')[1:-1][0]
        scientific_name = scientific_name.split('\t')[0]
    except IndexError:
        loggingC.message(f"\nERROR: No scientific name found for {sample_accession}. After submission, it can take some hours before an accession can be found through the ENA search. Please check if you can find this accession using the search function of the web interface.", threshold=-1)
        sys.exit(1)

    if ',' in scientific_name:
        loggingC.message(f"\nERROR: Multiple scientific names found for sample {sample_accession}:\n{scientific_name}", threshold=-1)
        sys.exit(1)

    return scientific_name


if __name__ == "__main__":
    # For debugging
    print("DEBUG: Checking API availability...\n")
    print("DEBUG: Running sample_accession_exists('SAMEA113417025',False)")
    print(sample_accession_exists('SAMEA113417025',False))
    print("DEBUG: Running sample_accession_exists('ERS28162653', False)")
    print(sample_accession_exists('ERS28162653', False))
    print("DEBUG: Running study_exists('PRJEB71644', False)")
    print(study_exists("PRJEB71644", False))
    print("DEBUG: Running search_scientific_name_by_sample('SAMEA114749859', False)")
    print(search_scientific_name_by_sample("SAMEA114749859", False))
    print("DEBUG: Running search_samples_by_assembly_analysis('ERZ1049590', False)")
    print(search_samples_by_assembly_analysis('ERZ1049590', False))
    print("DEBUG: Running sample_alias_accession('bgp35_d1a', 'PRJEB39821', False)")
    print(sample_alias_accession('bgp35_d1a', 'PRJEB39821', False))
    print("DEBUG: Running sample_title_accession('bgp35_digester_1_a', 'PRJEB39821', False)")
    print(sample_title_accession('bgp35_digester_1_a', 'PRJEB39821', False))
    print("DEBUG: Running read_name_accession('BGP350_Hc_deepseq', 'PRJEB39821', False)")
    print(run_alias_accession('BGP350_Hc_deepseq', 'PRJEB39821', False))
    print("DEBUG: Running search_scientific_name_by_sample('SAMEA114745644', False)")
    print(search_scientific_name_by_sample('SAMEA114745644', False))