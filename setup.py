#!/usr/bin/env python
import sys

from setuptools import setup, find_packages
from setuptools.command.install import install

class CustomInstall(install):
    def run(self):
        install.run(self)
        try:
            import tkinter
        except ImportError:
            print("\nERROR: 'tkinter' is not installed on your system.")
            if sys.platform.startswith("linux"):
                
                print("To install tkinter, run one of the following commands:")
                print("  Ubuntu/Debian: sudo apt install python3-tk")
                print("  Fedora/CentOS: sudo dnf install python3-tkinter")
                print("  Arch Linux: sudo pacman -S tk")
            elif sys.platform == "darwin":
                print("Please install tkinter to use the GUI.")
            elif sys.platform.startswith("win"):
                print("On Windows, 'tkinter' is included by default with the Python installer.")
                print("Ensure you have the official Python installed from https://www.python.org/downloads/.")
            else:
                print("Please refer to your operating system's documentation for installing 'tkinter'.")
        print("\nIMPORTANT: Please run the 'submg-cli download-webin' command.")

setup(
    name='submg',
    version='1.0.1',
    packages=find_packages(),
    install_requires=[
        'pysam>=0.19.1; sys_platform != "win32"',
        'PyYAML>=5.4.1',
        'requests>=2.31.0',
        'tqdm>=4.64.1',
        'yaspin>=2.0',
        'customtkinter>=5.2.2',
        'Pillow>=10.4.0',
    ],
    include_package_data=True,
    package_data={
        'submg.resources': ['*.png'],
        'submg': ['*.yaml', '*.fa', '*.fasta', '*.fasta.fai', '*.bam', '*.bam.bai', '*.tsv', '*.txt']
    },
    entry_points={
        'console_scripts': [
            'submg=submg.main:main',
            'submg-cli=submg.cli_main:main',
            'submg-gui=submg.gui_main:main',
        ],
    },
    cmdclass={
        'install': CustomInstall,
    },

    # Metadata
    author='ttubb',
    author_email='t.tubbesing@uni-bielefeld.de',
    description='A tool for submitting metagenomics study data to the European Nucleotide Archive',
    keywords='Metagenome, MAG, ENA, Submission',
    url='https://github.com/metagenomics/submg',
)
