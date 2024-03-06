#!/usr/bin/env python

from setuptools import setup, find_packages
from setuptools.command.install import install

class CustomInstall(install):
    def run(self):
        install.run(self)
        print("\nIMPORTANT: Please run the 'synum download_webin' command.")

setup(
    name='synum',
    version='0.9.1',
    packages=find_packages(),
    install_requires=[
        'pysam>=0.19.1',
        'PyYAML>=5.4.1',
        'Requests>=2.31.0',
        'tqdm>=4.64.1',
        'yaspin>=2.0',
    ],
    scripts=[
        'synum/main.py',
    ],
    include_package_data=True,
    package_data={
        'synum': ['*.yaml','*.fa','*.fasta','*.fasta.fai','*.bam','*.bam.bai','*.tsv','*.txt']
    },
    entry_points={
        'console_scripts': [
            'synum=synum.main:main'
        ],
    },
    cmdclass={
        'install': CustomInstall,
    },
    # Metadata
    author='ttubb',
    author_email='t.tubbesing@uni-bielefeld.de',
    description='A tool for submitting metagenome data to ENA',
    keywords='Metagenome, MAG, ENA, Submission',
    url='https://github.com/ttubb/synum',
)
