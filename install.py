#!/usr/bin/env python3

"""
Created on Mon Nov 27 17:10:10 2023

@author: ttubb
"""

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
    print("Java 1.8 or newer is required to run webin-cli.")
    try:
        output = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT)
        print(f"\tFound Java: {output}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit("\tUnable to detect Java version. Please install Java.")

def download_webin_cli(version):
    url = f"https://github.com/enasequence/webin-cli/releases/download/{version}/webin-cli-{version}.jar"
    print(f">Trying to download Webin-CLI from {url}")
    response = requests.get(url)
    if response.status_code == 200:
        with open(f"webin-cli-{version}.jar", 'wb') as file:
            file.write(response.content)
        print(">Webin-CLI downloaded successfully.")
    else:
        print("#####")
        print(f">WARNING: Failed to download Webin-CLI. Please download version {version} manually from the ENA website and place it in the same directory as this script.")
        print("#####")

def read_readme(fname='README.md'):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

def read_requirements(fname='requirements.txt'):
    with open(fname) as f:
        return f.read().strip().split('\n')

toolVersion, webinCliVersion = versions()
print(f">Versions: tool={toolVersion}, webin-cli={webinCliVersion}")

print(">Checking Java installation...")
check_java()
print("")

download_webin_cli(webinCliVersion)
print("")

print("To install all dependencies please run:")
print("pip3 install -r requirements.txt")