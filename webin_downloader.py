#!/usr/bin/env python

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
        sys.exit("\tUnable to detect Java version. Please install Java.")

def download_webin_cli(version):
    """ Downloads the webin-cli .jar file from the ENA website.
    """
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

def main():
    """ Checks if Java is installed and downloads the webin-cli .jar file
        from the ENA website.
    """
    toolVersion, webinCliVersion = versions()
    print(f">Versions: tool={toolVersion}, webin-cli={webinCliVersion}")
    print(">Checking Java installation...")
    check_java()
    print("")
    download_webin_cli(webinCliVersion)
    
if __name__ == "__main__":
    main()
    