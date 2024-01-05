import subprocess
import os
import glob

def find_webin_cli_jar():
    """ Find the Webin CLI JAR file in the parent directory of this script.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
    
    jar_files = glob.glob(os.path.join(parent_dir, 'webin*.jar'))
    
    if len(jar_files) == 1:
        return jar_files[0]
    elif len(jar_files) > 1:
        print(f"ERROR: Multiple webin-cli .jar files found in {parent_dir}. Please ensure there's only one.")
        exit(1)
    else:
        print(f"ERROR: webin_cli .jar file not found in {os.path.abspath(parent_dir)}.\nYou can download the .jar using install.py or from the ENA website.")
        exit(1)

def __webin_cli_validate(manifest,
                         inputdir,
                         outputdir,
                         username,
                         password,
                         test,
                         context,
                         jar,
                         verbose=1):
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
        if verbose<1:
            subprocess.run(cmd,
                           stdout = subprocess.DEVNULL,
                           stderr = subprocess.DEVNULL,
                           check=True)
        else:
            subprocess.run(cmd,
                           check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Validation failed with error: {e}") 

def __webin_cli_submit(manifest,
                       inputdir,
                       outputdir,
                       username,
                       password,
                       test,
                       context,
                       jar,
                       verbose=1):
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
        if verbose>0:
            print("Using test submission service")
        cmd.append('-test')
    else:
        if verbose>0:
            print("Using production submission service")
    
    try:
        if verbose<1:
            subprocess.run(cmd,
                           stdout = subprocess.DEVNULL,
                           stderr = subprocess.DEVNULL,
                           check=True)
        else:
            subprocess.run(cmd,
                           check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Submission failed with error: {e}")


def webin_cli(manifest,
              inputdir,
              outputdir,
              username,
              password,
              subdir_name,
              submit=False,
              test=True,
              context='genome',
              verbose=1):
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
        if verbose>1:
            print(f"Submitting {subdir_name} to ENA through webin-cli")
        __webin_cli_submit(manifest,
                           inputdir,
                           outputdir,
                           username,
                           password,
                           test,
                           context,
                           jar,
                           verbose)
        receipt = os.path.join(outputdir, 'genome', subdir_name.replace(' ','_'), 'submit', 'receipt.xml')
    else:
        if verbose>1:
            print(f"Validating {subdir_name} for ENA submission using webin-cli")
        __webin_cli_validate(manifest,
                             inputdir,
                             outputdir,
                             username,
                             password,
                             test,
                             context,
                             jar,
                             verbose)
        receipt = None

    return receipt
