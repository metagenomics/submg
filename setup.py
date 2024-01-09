import sys
import subprocess
import requests
from setuptools import setup, find_packages
from setuptools.command.install import install
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

class CustomInstall(install):
    def run(self):
        # Custom additions
        toolVersion, webinCliVersion = versions()
        print(f">Versions: tool={toolVersion}, webin-cli={webinCliVersion}")
        print(f">Checking Java installation...")
        check_java()
        print(f">Downloading Webin-CLI from ENA...")
        download_webin_cli(webinCliVersion)
        print(f">Starting setup\n")

        # Call the standard install command
        install.run(self)

setup(
    name='synum',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pysam>=0.19.1',
        'PyYAML>=5.4.1',
        'Requests>=2.31.0',
        'tqdm>=4.64.1',
        'yaspin>=3.0.1',
    ],
    scripts=[
        'synum/synum.py',
    ],
    include_package_data=True,
    package_data={
        'synum': ['*.yaml','*.fa','*.fasta','*.fasta.fai','*.bam','*.bam.bai','*.tsv','*.txt']
    },
    entry_points={
        'console_scripts': [
            'synum=synum.synum:main'
        ],
    },
    cmdclass={
        'install': CustomInstall,
    },
    # Metadata
    author='ttubb',
    author_email='t.tubbesing@uni-bielefeld.de',
    description='A tool for submitting metagenomes and metagenome bins to ENA',
    keywords='Metagenome, MAG, ENA, Submission',
    url='https://github.com/ttubb/synum',
)
