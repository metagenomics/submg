#!/usr/bin/env python

import os
import subprocess
import requests
import sys

from submg.modules import statConf


def versions():
    """ Reads in versions of this tool and the corresponding ENA
        webin_cli version from the VERSIONS file.
    """
    toolVersion = statConf.staticConfig.submg_version
    webinCliVersion = statConf.staticConfig.webin_cli_version
    return toolVersion, webinCliVersion


def check_java(soft=False):
    """ Checks if Java is installed.

        Args:
            soft (bool): If True, the function will return True if Java is 
            installed and False if it is not. If False, the function will exit 
            the program if Java is not installed.
    """
    java_version = statConf.staticConfig.java_version
    try:
        output = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT)
        if soft:
            return True
        print(f"\tFound Java: {output}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        if soft:
            return False
        sys.exit(f"\tfUnable to detect Java version. Please install Java "
                 f"({java_version} or higher).")


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