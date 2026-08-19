import argparse
from datetime import datetime
from functools import partial
import re
import sys
import tempfile
import traceback

import requests
from requests.exceptions import ConnectionError, ConnectTimeout, HTTPError, RequestException


from submg.modules import loggingC
from submg.modules.statConf import staticConfig


_standalone_diagnostic_mode = False



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


def _search_request(url: str, params: dict):
    """Run an ENA Search API request and report its URL in diagnostic mode."""
    prepared_url = requests.Request("GET", url, params=params).prepare().url
    try:
        response = requests.get(url, params=params)
    except Exception:
        if _standalone_diagnostic_mode:
            print(f"Request URL: {prepared_url}")
        raise

    if _standalone_diagnostic_mode:
        print(f"Request URL: {getattr(response, 'url', prepared_url)}")
    return response


def _log_unexpected_response(resource: str,
                             accession: str,
                             response):
    """Log the details of an unexpected ENA search response."""
    response_text = response.text.strip()
    request_url = (
        ""
        if _standalone_diagnostic_mode
        else f"\tRequest URL: {response.url}\n"
    )
    message = (
        f"\nERROR: Unexpected response when querying ENA API for "
        f"{resource} accession {accession}.\n"
        f"\tHTTP status: {response.status_code}\n"
        f"{request_url}"
    )

    if not _standalone_diagnostic_mode:
        message += "\tResponse body:\n\n"

    if _standalone_diagnostic_mode:
        if response_text:
            formatted_response = "\n".join(
                f"\tENA Response: {line}" if index == 0 else f"\t{line}"
                for index, line in enumerate(response_text.splitlines())
            )
        else:
            formatted_response = "\tENA Response: <empty>"
        message += formatted_response
    else:
        message += (
            f"--- BEGIN ENA RESPONSE ---\n{response.text}\n"
            f"--- END ENA RESPONSE ---\n\n"
            f"NOTE: In the past, such unexepected responses have "
            f"been caused by temporary ENA server issues. "
            f"We recommend you check https://www.ebi.ac.uk/ena/browser/service-status "
            f"and/or trying again tomorrow before making changes "
            f"to your submission."
        )

    loggingC.message(message, threshold=-1)


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
    response = _search_request(url, params)

    data = response.text.split('\n')
    if (len(data) < 2) or (data[0] != 'study_accession') or (data[1] not in [study_accession, '']):
        # There are some weird issues when querying the development server API
        # So if the query fails we try to find the study on the production
        # server. This _might_ lead to issues when the study is not yet
        # available on dev.
        if devserver:
            if _standalone_diagnostic_mode:
                print("Automatic fallback canceled since this is debug mode")
            else:
                return study_exists(study_accession, False)
        _log_unexpected_response("study", study_accession, response)
        sys.exit(1)
    if data[1] == study_accession:
        return True
    return False


def _sample_accession_query_field(sample_accession: str) -> str:
    """Return the ENA Search API field for a sample accession format."""
    if sample_accession.upper().startswith("ERS"):
        return "secondary_sample_accession"
    return "sample_accession"


def sample_accession_exists(sample_accession: str,
                            devserver: bool = False) -> bool:
    """
    Check if a sample with the input accession exists in ENA.

    Args:
        sample_accession (str): A primary (SAMEA) or secondary (ERS) sample
                                accession.
        devserver (bool):        Whether to use the test server.

    Returns:
        bool: True if the sample exists, False if not.
    """
    if devserver:
        url = staticConfig.ena_test_search_url
    else:
        url = staticConfig.ena_search_url
    ensure_server_online(url)

    query_field = _sample_accession_query_field(sample_accession)
    params = {
        "query": f"{query_field}={sample_accession}",
        "result": "sample",
        "fields": "sample_accession"
    }
    response = _search_request(url, params)

    data = response.text.split('\n')
    returned_accession = data[1] if len(data) > 1 else ''
    if ((len(data) < 2)
            or (data[0] != 'sample_accession')
            or (returned_accession
                and re.fullmatch(
                    r'SAM(?:E|D|N)[A-Z]?\d+', returned_accession
                ) is None)
            or (query_field == 'sample_accession'
                and returned_accession not in [sample_accession, ''])):
        _log_unexpected_response("sample", sample_accession, response)
        sys.exit(1)
    return returned_accession != ''


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
    response = _search_request(url, params)
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
    response = _search_request(url, params)
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
    response = _search_request(url, params)
    data = response.text.split('\n')
    if ((response.status_code != 200)
            or (len(data) < 2)
            or (data[0] != 'run_accession')
            or any(row.lstrip().upper().startswith('ERROR')
                   for row in data[1:])):
        _log_unexpected_response("run alias", run_alias, response)
        sys.exit(1)
    data = data[1]
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
    response = _search_request(url, params)

    try:
        sample_accession = response.text.split('\n')[1:-1][0]
        sample_accession = sample_accession.split('\t')[1].strip()
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
    response = _search_request(url, params)
    try:
        scientific_name = response.text.split('\n')[1:-1][0]
        scientific_name = scientific_name.split('\t')[1].strip()
    except IndexError:
        loggingC.message(f"\nERROR: No scientific name found for {sample_accession}. After submission, it can take some hours before an accession can be found through the ENA search. Please check if you can find this accession using the search function of the web interface.", threshold=-1)
        sys.exit(1)

    if ',' in scientific_name:
        loggingC.message(f"\nERROR: Multiple scientific names found for sample {sample_accession}:\n{scientific_name}", threshold=-1)
        sys.exit(1)

    return scientific_name


def _diagnostic_checks(devserver: bool):
    """ Returns a list of diagnostic checks to run against the ENA Search API.
        Each check is a tuple of (name, expected result, callable).

        Args:
            devserver (bool): Whether to use the test server.
    """
    specifications = [
        (sample_accession_exists, ("SAMEA113417025",), "True (Exists on Dev and Prod)"),
        (sample_accession_exists, ("ERS28162653",), "True (Exists on Dev and Prod)"),
        (study_exists, ("PRJEB71644",), "True (Exists on Dev and Prod)"),
        (
            search_scientific_name_by_sample,
            ("SAMEA114749859",),
            "uncultured bacterium",
        ),
        (
            search_samples_by_assembly_analysis,
            ("ERZ1049590",),
            "SAMEA5841080",
        ),
        (
            sample_alias_accession,
            ("bgp35_d1a", "PRJEB39821"),
            "SAMEA113417017 ",
        ),
        (
            sample_title_accession,
            ("bgp35_digester_1_a", "PRJEB39821"),
            "SAMEA113417017",
        ),
        (
            run_alias_accession,
            ("BGP350_Hc_deepseq", "PRJEB39821"),
            "ERR11585864",
        ),
        (
            search_scientific_name_by_sample,
            ("SAMEA114745644",),
            "biogas fermenter metagenome ",
        ),
        (
            sample_accession_exists,
            ("SAMEA00000000",),
            "False (Does not exist on Dev or Prod)",
        ),
    ]

    return [
        (
            f"{function.__name__}({', '.join(repr(arg) for arg in args)})",
            expected,
            partial(function, *args, devserver=devserver),
        )
        for function, args, expected in specifications
    ]


def _parse_diagnostic_args() -> argparse.Namespace:
    """Parse the server selection for standalone API diagnostics."""
    parser = argparse.ArgumentParser(
        description="Run diagnostic checks against the ENA Search API."
    )
    parser.add_argument(
        "server",
        nargs="?",
        choices=("prod", "dev"),
        metavar="{prod,dev}",
        help="ENA server to query: prod or dev",
    )
    args = parser.parse_args()
    if args.server is None:
        parser.error("please specify one of the two servers: 'prod' or 'dev'")
    return args


def _run_diagnostics(server: str) -> int:
    """Run all standalone API diagnostics and return a process exit code."""
    global _standalone_diagnostic_mode

    devserver = server == "dev"
    server_name = "development" if devserver else "production"
    search_url = (
        staticConfig.ena_test_search_url
        if devserver
        else staticConfig.ena_search_url
    )
    checks = _diagnostic_checks(devserver)
    passed = 0
    failed = 0
    unavailable = 0

    print(f"DEBUG: Checking ENA Search API ({server_name} server).")
    print(f"DEBUG: Endpoint: {search_url}")
    print(f"DEBUG: Running {len(checks)} diagnostic checks.\n")

    # We need a logfile for direct execution
    previous_diagnostic_mode = _standalone_diagnostic_mode
    _standalone_diagnostic_mode = True
    try:
        with tempfile.TemporaryDirectory(prefix="ena_search_diagnostics_") as log_dir:
            timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S_%f")
            loggingC.set_up_logging(log_dir, verbose=2, timestamp=timestamp)
            print(f"DEBUG: Temporary log file: {loggingC.logfile_path}\n")

            for index, (name, expected, check) in enumerate(
                checks, start=1
            ):
                print(f"[{index}/{len(checks)}] {name}")
                print(f"Expected: {expected}")

                try:
                    result = check()
                except SystemExit as exc:
                    unavailable += 1
                    print(
                        f"Result: ERROR (diagnostic exited with status {exc.code})",
                        file=sys.stderr,
                    )
                    print(
                        f"Context: server={server}, endpoint={search_url}",
                        file=sys.stderr,
                    )
                    print()
                    continue
                except Exception as exc:
                    failed += 1
                    print("Result: UNEXPECTED EXCEPTION", file=sys.stderr)
                    print(f"Exception: {type(exc).__name__}: {exc}", file=sys.stderr)
                    print(
                        f"Context: test={name}; server={server}; endpoint={search_url}",
                        file=sys.stderr,
                    )
                    print(
                        f"Logging state: logfile_path={loggingC.logfile_path!r}; "
                        f"verbosity_level={loggingC.verbosity_level!r}",
                        file=sys.stderr,
                    )
                    traceback.print_exc()
                    print()
                    continue

                passed += 1
                print(f"Result: {result!r}")
                print()

            print("Diagnostic summary:")
            print(f"  Completed: {passed}")
            print(f"  Unexpected exceptions: {failed}")
            print(f"  API errors/unavailable: {unavailable}")
    finally:
        _standalone_diagnostic_mode = previous_diagnostic_mode

    return 0 if failed == 0 and unavailable == 0 else 1


if __name__ == "__main__":
    arguments = _parse_diagnostic_args()
    sys.exit(_run_diagnostics(arguments.server))
