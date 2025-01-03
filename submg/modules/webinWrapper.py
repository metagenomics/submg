import subprocess
import os
import glob
import signal

from . import loggingC
from .statConf import staticConfig


def webin_cli_jar_available():
    """ Check if the Webin CLI JAR file is present in the directory of this
        script. Then check if it corresponds to the expected version.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    jar_files = glob.glob(os.path.join(script_dir, 'webin*.jar'))
    version_string = staticConfig.webin_cli_version
    expected_filename = f"webin-cli-{version_string}.jar"
    # Check if any JAR file corresponds to this version
    for jar_file in jar_files:
        if os.path.basename(jar_file) == expected_filename:
            return True
    # Log warning (either no JAR file found or wrong version)
    if len(jar_files) == 0:
        warn = (f"WARNING: webin-cli .jar file not found in "
                f"{os.path.abspath(script_dir)}. ")
    else:
        warn = (f"WARNING: webin-cli .jar file found in "
                f"{os.path.abspath(script_dir)}\n "
                f"but it does not match the expected version "
                f"{version_string}. ")
    warn += (f"To download webin-cli, use the GUI or run the following "
             f"command:\nsubmg-cli download_webin")
    loggingC.message(warn, threshold=0)
    return False


def find_webin_cli_jar():
    """ Find the Webin CLI JAR file in the directory of this script.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    #parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
    
    jar_files = glob.glob(os.path.join(script_dir, 'webin*.jar'))
    
    if len(jar_files) == 1:
        return jar_files[0]
    elif len(jar_files) > 1:
        err = f"ERROR: Multiple webin-cli .jar files found in {os.path.abspath(script_dir)}. Please ensure there's only one."
        loggingC.message(err, threshold=-1)
        exit(1)
    else:
        err = f"ERROR: webin_cli .jar file not found in {os.path.abspath(script_dir)}.\nYou can download the .jar by running the webin_downloader.py file in the submg/modules directory or manually from the ENA website."
        loggingC.message(err, threshold=-1)
        exit(1)


def __webin_cli_validate(manifest,
                         inputdir,
                         outputdir,
                         username,
                         password,
                         test,
                         context,
                         jar):
    cmd = [
        'java',
        '-jar',
        jar,
        '-validate',
        f'-username={username}',
        f'-password={password}',
        f'-inputdir={inputdir}',
        f'-outputdir={outputdir}',
        f'-context={context}',
        f'-manifest={manifest}'
    ]
    try:
        # Run the subprocess and capture stdout and stderr
        result = subprocess.run(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,  # Ensures the output is in string format
                                check=True)

        # Log the stdout if any
        if result.stdout:
            loggingC.message(result.stdout.strip().replace('\n','; '), threshold=0)

        # Log the stderr if any
        if result.stderr:
            loggingC.message(result.stderr.strip().replace('\n','; '), threshold=0)

    except subprocess.CalledProcessError as e:
        # Even if the subprocess fails, it may produce output or errors, so capture and log them
        if e.stdout:
            loggingC.message(e.stdout.strip().replace('\n','; '), threshold=-1)
        if e.stderr:
            loggingC.message(e.stderr.strip().replace('\n','; '), threshold=-1)

        # Finally, log the exception itself
        loggingC.message(f"\nERROR: Validation failed with error: {e}", threshold=-1)

        
def __webin_cli_submit(manifest,
                       inputdir,
                       outputdir,
                       username,
                       password,
                       test,
                       context,
                       jar):
    cmd = [
        'java',
        '-jar',
        jar,
        '-submit',
        f'-username={username}',
        f'-password={password}',
        f'-inputdir={inputdir}',
        f'-outputdir={outputdir}',
        f'-context={context}',
        f'-manifest={manifest}'
    ]
    
    if test:
        loggingC.message("\n           Submitting to development service through Webin-CLI", threshold=0)
        cmd.append('-test')
    else:
        loggingC.message("\n           Submitting to PRODUCTION service through Webin-CLI", threshold=0)
    try:
        process = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True)
    except KeyboardInterrupt:
        process.send_signal(signal.SIGINT)
    
    accession = None
    if context == 'genome':
        accession_line = staticConfig.webin_analysis_accession_line
    elif context == 'reads':
        accession_line = staticConfig.webin_run_accessions_line
    else:
        raise ValueError(f"ERROR: Invalid context {context}")
    for line in iter(process.stdout.readline, ''):
        if accession_line in line:
            accession = line.strip().split(' ')[-1]

        if line.startswith('INFO : '):
            line = line[7:].strip()
        line = line.replace('\n',' ')
        loggingC.message(f"Webin-CLI: {line}", threshold=0)

    process.wait()

    return accession


def webin_cli(manifest,
              inputdir,
              outputdir,
              username,
              password,
              subdir_name,
              submit=False,
              test=True,
              context='genome'):
    """
    Submit or validate data to/from the Webin submission system.

    Args:
        manifest (str): The path to the manifest file containing submission details
        inputdir (str): The directory where manifest + files referenced in manifest are located
        outputdir (str): webin_cli submission reports will go here
        username (str): username for ENA authentication
        password (str): password for ENA authentication
        submit (bool, optional): If True, the method will submit the data; if False, it will only validate (default is False).
        test (bool, optional): If True, use the Webin test submission service (default is True).
        context (str, optional): The context for the submission (e.g., 'genome', 'transcriptome', etc.) (default is 'genome').
    """
    jar = find_webin_cli_jar()
    if submit:
        loggingC.message(f">Using ENA Webin-CLI to submit {subdir_name}", threshold=2)
        accession = __webin_cli_submit(manifest,
                                        inputdir,
                                        outputdir,
                                        username,
                                        password,
                                        test,
                                        context,
                                        jar)
        receipt = os.path.join(outputdir, context, subdir_name.replace(' ','_'), 'submit', 'receipt.xml')
        if accession is None:
            err =  f"ERROR: The submission failed for {inputdir}."
            err += f" If the submission failed during validation, please consult the output of Webin-CLI."
            err += f" Otherwise please check the receipt at {receipt}"
            loggingC.message(err, threshold=-1)
            exit(1)
    else:
        loggingC.message(f">Validating {subdir_name} for ENA submission using webin-cli", threshold=1)
        __webin_cli_validate(manifest,
                             inputdir,
                             outputdir,
                             username,
                             password,
                             test,
                             context,
                             jar)
        receipt = None

    return receipt, accession
