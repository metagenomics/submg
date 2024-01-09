
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="synum/logo_dark.png">
  <source media="(prefers-color-scheme: light)" srcset="synum/logo_light.png">
  <img alt="Synom Logo" src="synum/logo_light.png">
</picture>
&nbsp;

&nbsp;
![GitHub release (latest by date)](https://img.shields.io/github/v/release/ttubb/synum)


# synum
Synum aids in the submission of (co-)metagenome assemblies as well es MAG bins to the European Nucleotide Archive (ENA). After you enter your (meta)data in single YAML form, Synum derives additional information where required, creates all samplesheets and manifests and uploads everything to your ENA account. The tool will not work for non-metagenome submissions.

Be aware that the [ENA definition of a MAG](https://ena-docs.readthedocs.io/en/latest/submit/assembly/metagenome/mag.html#what-is-considered-a-mag-in-ena) (Metagenome Assembled Genome) is different from a metagenome bin and that bins should be submitted before MAGs. We plan to support MAG upload in the future. In case you intend to upload assemblies assembled from third party data, [ENA ask you to contact their helpdesk](https://ena-docs.readthedocs.io/en/latest/submit/assembly/metagenome/mag.html#introduction).


- [Installation](#installation)
- [Usage](#usage)
  * [Prerequisites](#prerequisites)
  * [ENA Development Test Server](#ena-development-test-server)
  * [The Config File](#the-config-file)
  * [Arguments](#arguments)
  * [Examples](#examples)
    + [Uploading an Assembly](#uploading-an-assembly)
    + [Uploading Bins](#uploading-bins)
    + [Uploading an Assembly and Bins](#uploading-an-assembly-and-bins)
- [Taxonomy Assignment](#taxonomy-assignment)
- [Dereplication](#dereplication)
- [Bin Contamination above 100%](#bin-contamination-above-100-percent)
- [Support](#support)


# Installation
- Make sure Python 3.10 or higher is installed
- Make sure Java 1.8 or higher is installed
- Clone this repository (`git clone https://github.com/ttubb/synum`)
- Switch into the directory that you just cloned
- Run `python -m pip install .`
- Run `python3 webin_downloader.py` which will download a compatible version of the `.jar` file for [ENA's Webin-CLI tool](https://github.com/enasequence/webin-cli). 

# Usage

## Prerequisites
Before you can upload assemblies and bins with synum, you need to have a `Study` object in your ENA account. Before using Synum, you also need to upload all reads and create objects for all biological samples. For instructions on these steps see the [ENA documentation](https://ena-docs.readthedocs.io/en/latest/).

## ENA Development Test Server
ENA provides a [test service](https://ena-docs.readthedocs.io/en/latest/submit/general-guide/interactive.html) to trial your submission. We strongly suggest submitting to the production server only after a test submission with identical parameters was successful. Otherweise, you might end up with incomplete or incorrect submissions, with no ability to correct or remove them. Unless `--devtest 0` is specified, synum will always submit to the test server.

## The Config File
A lot of (meta)data is required for a submission. To use synum, you need to provide metadata and the locations of your files in a YAML document. We recommend filling out the fields in `exampleConfig.yaml`, which also contains comments with explanations for each field. The file is divided into sections. Which sections you need to fill out depends on the type of your submission and is explained in the comments of `exampleConfig.yaml`. You may consult the config files in the `./tests` directory to see more examples. If you are unsure of how to fill out certain fields, you can ask in the [github discussions page](https://github.com/ttubb/synum/discussions) of this project.

## Arguments
```
  -h, --help            show this help message and exit
  -x CONFIG, --config CONFIG
                        Path to the YAML file containing metadata and filepaths. Mandatory
  -s STAGING_DIR, --staging_dir STAGING_DIR
                        Directory where files will be staged for upload. Must be empty. May use up a lot of disk space. Mandatory.
  -l LOGGING_DIR, --logging_dir LOGGING_DIR
                        Directory where log files will be stored. Must be empty. Mandatory.
  -a, --submit_assembly
                        Submit a primary metagenome assembly.
  -b, --submit_bins     Submit metagenome bins (note that bins are different from MAGs in the ENA definition).
  -y {0,1,2}, --verbosity {0,1,2}
                        Control the amount of logging to stdout. [default 1]
  -d {0,1}, --devtest {0,1}
                        Make submissions to the ENA dev test server. [default 1/true]
  -t THREADS, --threads THREADS
                        Number of threads used to process .bam files. [default 4]
  -k, --keep_depth_files
                        Do not delete depth files after running. [default false]
  -v, --version         show program's version number and exit
```

## Examples

### Uploading an Assembly
If you only want to upload a metagenome assembly, you might use `synum` like this:

```
python3 ./synum.py \
    --config /path/to/your/config.yaml \
    --staging_dir /path/to/your/staging_dir \
    --logging_dir /path/to/your/logging_dir \
    --submit_assembly 
```

An example of a config file for this specific use case can be found in `./tests/test4_config.yaml`. In the samplesheet, you have to provide the accessions of the biological sample the assembly is based on. If you provided one sample accession the tool will:
- Parse the `.bam` files you have provided to calculate coverage
- Create a manifest and stage it together with the `.fasta`file, then start an upload with ENA's Webin-CLI tool

If you have provided multiple sample accessions, the tool assumes that this is a co assembly and will:
- Parse the `.bam` files you have provided to calculate coverage
- Create a samplesheet with an entry for the "virtual sample" that represents the co-assembly, referencing the accessions of the biological samples, then upload it
- Create a manifest and stage it together with the `.fasta`file, then start an upload with ENA's Webin-CLI tool

### Uploading Bins
If you have already uploaded your assembly and only need to upload the bins, you might use `synum` like this:
```
python3 ./synum.py \
    --config /path/to/your/config.yaml \
    --staging_dir /path/to/your/staging_dir \
    --logging_dir /path/to/your/logging_dir \
    --submit_bins 
```
An example of a config file for this specific use case can be found in `./tests/test1_config.yaml`. The tool will:
- Try to determine valid taxonomies for each bin, based on the `NCBI_TAXONOMY_FILES` and `MANUAL_TAXONOMY_FILE` you have provided in the config
    - In some cases, automatic assignment of taxonomy is not possible. If that is the case, consult the section on [taxonomy assignment](#taxonomy-assignment) below.
- Parse the `.bam` files you have provided to calculate coverage
- Create a samplesheet with one entry for each bin and upload it
- Based on the accession assigned to the individual samples, create a manifest for each bin and stage it together with the `.fasta` files
- Upload the bins using ENA's Webin-CLI tool

### Uploading an Assembly and Bins
In case you want to upload your assembly and bins, you can use `synum` like this:
```
python3 ./synum.py \
    --config /path/to/your/config.yaml \
    --staging_dir /path/to/your/staging_dir \
    --logging_dir /path/to/your/logging_dir \
    --submit_assembly \
    --submit_bins
```
An example of a config file for this specific use case can be found in `./tests/test1_config.yaml`. The tool will first upload an assembly as described [above](#uploading-an-assembly) and then upload the bins as described [above](#uploading-bins).

# Taxonomy Assignment
Assemblies and bins need a valid NCBI taxonomy (scientific name and taxonomic identifier) for submission. If you did taxonomic annotation of bins based on [GTDB](https://gtdb.ecogenomic.org/), you can use the `gtdb_to_ncbi_majority_vote.py` script of the [GTDB-Toolkit](https://github.com/Ecogenomics/GTDBTk) to translate your results to NCBI taxonomy.

If you provide a tables with NCBI taxonomy information for each bin (see `./tests/bacteria_taxonomy.tsv` for an example - the output of `gtdb_to_ncbi_majority_vote.py` has the correct format already). Synum will use ENAs [suggest-for-submission-sendpoint](https://ena-docs.readthedocs.io/en/latest/retrieval/programmatic-access/taxon-api.html) to derive taxids that follow the [rules for bin taxonomy](https://ena-docs.readthedocs.io/en/latest/faq/taxonomy.html).

You can also provide specific taxids and scientific names for each bin in a document and specify it in the `MANUAL_TAXONOMY` field of your config file. An example of such a document can be found in `./tests/manual_taxonomy_3bins.tsv`. If a bin is present in this document, the taxonomic data from other tables will be ignored.

In some cases synum will be unable to assign a valid taxonomy to a bin. The submission will be aborted and you will be informed which bins are causing problems. In such cases you have to determine the correct scientific name and taxid for the bin and specify it in the `MANUAL_TAXONOMY` field of your config file. Sometimes the reason for a failed taxonomic assignment is that no proper taxid exists yet. You can [create a taxon request](https://ena-docs.readthedocs.io/en/latest/faq/taxonomy_requests.html) in the ENA Webin Portal to register the taxon.

# Dereplication
If your bins are the result of dereplicating data from a single assembly you can use synum as described above. If your bins are the result of dereplicating data from multiple different assemblies, you need to split them based on which assembly they belong to. You can then start synum seperately for each assembly (and corresponding set of bins).

# Bin Contamination above 100 percent
When calculating completeness and contamination of a bin with e.g. CheckM, contamination values above 100% can occur. [This is not an error](https://github.com/Ecogenomics/CheckM/issues/107). However, the ENA API will refuse to accept bins with contamination values above 100%. This issue is unrelated to synum, but to avoid partial submissions synum will refuse to submit data if it detects such a bin. If you have bins with contamination values above 100%, you can either leave them out by removing them from you dataset or manually set the contamination value to 100% in the `BINS_QUALITY_FILE` file you provide to synum.

# Support
Synum is being actively developed. Please use the github issue tracker to report problems. A discussions page is available for questions, comments or suggestions. 
