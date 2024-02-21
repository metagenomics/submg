#!/usr/bin/env python

import os
import subprocess
import requests
import sys

from synum import statConf

def versions():
    """ Reads in versions of this tool and the corresponding ENA
        webin_cli version from the VERSIONS file.
    """
    toolVersion = statConf.staticConfig.synum_version
    webinCliVersion = statConf.staticConfig.webin_cli_version
    return toolVersion, webinCliVersion

def check_java():
    """ Checks if Java is installed and reports the version.
    """
    print("Java 1.8 or newer is required to run webin-cli.")
    try:
        output = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT)
        print(f"\tFound Java: {output}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit("\tUnable to detect Java version. Please install Java (1.8 or newer).")

def download_webin_cli(version):
    """ Downloads the webin-cli .jar file from the ENA website.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    jar_path = os.path.join(script_dir, f"webin-cli-{version}.jar")
    url = f"https://github.com/enasequence/webin-cli/releases/download/{version}/webin-cli-{version}.jar"
    print(f">Trying to download Webin-CLI from {url}")
    response = requests.get(url)
    if response.status_code == 200:
        with open(jar_path, 'wb') as file:
            file.write(response.content)
        print(">Webin-CLI downloaded successfully.")
    else:
        print("#####")
        print(f">WARNING: Failed to download Webin-CLI. Please download version {version} manually from the ENA website and place it in the same directory as this script.")
        print("#####")