
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="submg/img/logo_dark.png">
  <source media="(prefers-color-scheme: light)" srcset="submg/img/logo_light.png">
  <img alt="submg Logo" sr c="submg/img/logo_light.png">
</picture>

&nbsp;
&nbsp;
# About <img align="right" style="float: right; margin-left: 10px; margin-top: 15px;" src="https://img.shields.io/github/v/release/ttubb/synum" alt="GitHub release (latest)">
submg aids in the submission of metagenomic study data to the European Nucleotide Archive. It can be used to submit various combinations of samples, reads, (co-)assemblies, bins and MAGs. After you enter your (meta)data in single YAML form, submg derives additional information where required, creates samplesheets and manifests and uploads everything to your ENA account.


<picture>
  <source media="(prefers-color-scheme: dark)" srcset="submg/img/steps_dark.png">
  <source media="(prefers-color-scheme: light)" srcset="submg/img/steps_light.png">
  <img alt="Steps of submitting data with submg" src="submg/img/steps_light.png">
</picture>

&nbsp;
&nbsp;

Please Note
1. The tool will work *only* for metagenomic data.
2. The [ENA definition of a MAG](https://ena-docs.readthedocs.io/en/latest/submit/assembly/metagenome/mag.html#what-is-considered-a-mag-in-ena) (Metagenome Assembled Genome) is different from a metagenomic bin. Bins should be submitted before MAGs.
3. In case you intend to upload results based on third party data, [ENA ask you to contact their helpdesk](https://ena-docs.readthedocs.io/en/latest/submit/assembly/metagenome/mag.html#introduction).
4. Please [report any issues](https://github.com/ttubb/submg/issues/new) you have with this tool. We'll get back to you as soon as possible.
5. If the tool doesn't cover your use case, [let us know](https://github.com/ttubb/submg/discussions). We are happy to expand functionality.


# Content
- [Installation](#installation)
- [Usage](#usage)
  * [Example](#example)
  * [ENA Development Service](#ena-development-service)
  * [Study Object](#study-object)
  * [The Config File](#the-config-file)
  * [MAG Submission](#mag-submission)
    + [Contig- and Chromosome-MAG-Assemblies](#contig--and-chromosome-mag-assemblies)
    + [MAG metadata](#mag-metadata)
  * [Preventing Process Interruption](#preventing-process-interruption)  
- [Taxonomy Assignment](#taxonomy-assignment)
  * [NCBI Taxonomy File](#ncbi-taxonomy-file)
  * [Manual Taxonomy File](#manual-taxonomy-file)
- [Dereplication](#dereplication)
- [Bin Contamination above 100%](#bin-contamination-above-100-percent)
- [Support](#support)


# Installation
- Make sure Python 3.8 or higher is installed
- Make sure Java 1.8 or higher is installed
- Make sure [wheel](https://pypi.org/project/wheel/) is installed
- Clone this repository: `git clone https://github.com/ttubb/submg`
- Switch into the directory that you just cloned
- Run `python -m pip install .`
- Run `submg download_webin` which will download a compatible version of the `.jar` file for [ENA's Webin-CLI tool](https://github.com/enasequence/webin-cli). 

# Usage
submg is intended to submit data related to a *single* (co-)assembly. All samples, sequncing runs, bins and MAGs specified in the config file will be associated with this assembly. If you want to submit data from multiple assemblies, you need to run submg once for each assembly.

## Example
Assuming you want to upload 2 samples, 2 paired-end read files, a co-assembly and bins. We will collect the necessary data, do a test submission, then upload everything to the ENA.

1 - Create environment variables for your ENA username and password:
```
export ENA_USER=your_ena_username
export ENA_PASSWORD=your_ena_password
```
2 - Create study object through the web interface of the [ENA development service](https://wwwdev.ebi.ac.uk/ena/submit/webin/login)

3 - Create a template config file using:
```
submg makecfg --outfile /path/to/your/config.yaml --submit_samples 2 --submit_paired_end_reads 2 --submit_assembly --submit_bins
```
4 - Fill out the config file (it contains explanations and examples for each line)

5 - Submit your data to the development server using:
```
submg submit --config /path/to/your/config.yaml --staging_dir /path/to/empty/directory1 --logging_dir /path/to/empty/directory2 --submit_samples --submit_reads --submit_assembly --submit_bins
```
6 - If there are no errors, create a study object through the web interface of the [ENA production server](https://www.ebi.ac.uk/ena/submit/webin/login)

7 - Submit your data to the production server using
```
submg submit --config /path/to/your/config.yaml --staging_dir /path/to/empty/directory3 --logging_dir /path/to/empty/directory4 --submit_samples --submit_reads --submit_assembly --submit_bins --development_service 0
```

## ENA Development Service
ENA provides a [development service](https://ena-docs.readthedocs.io/en/latest/submit/general-guide/interactive.html) to trial your submission before uploading your data to the production server. We strongly suggest submitting to the production server only after a test submission with identical parameters was successful. Otherwise, you might end up with incomplete or incorrect submissions, with no ability to correct or remove them. Unless `--development_service 0` is specified, submg will always submit to the test server.

## Study Object
`Study` is used synonymously with `project` here. Before you can submit data using submg, you need to have a `Study` object (= a project) in your ENA account. If you intend to submit annotation data, you will also need a [locus tag prefix](https://ena-docs.readthedocs.io/en/latest/faq/locus_tags.html). You can create both through the ENA webin portal on the [production server](https://www.ebi.ac.uk/ena/submit/webin/login) or the [development server](https://wwwdev.ebi.ac.uk/ena/submit/webin/login). Be aware that if you create the `Study` object on the production server, it can take up to 24h hours until it is available on the development server. This can cause test submissions to fail.

## The Config File
A lot of (meta)data is required for a submission. To use submg, you need to provide metadata and the locations of your files in a YAML document. Which information is required depends on the type of your submission. You can use `submg makecfg` command to create a template for your config file. It will contain only the fields necessary for your specific submission, along with explanations and examples. Additionally, the `examples` directory contains examples of config files and the associated data. If you are unsure of how to fill out certain fields, please feel free to ask on the [github discussions page](https://github.com/ttubb/submg/discussions) of this project.

## MAG Submission
If you have assembled high quality bins from your metagenome, you can [submit them as MAGs](https://ena-docs.readthedocs.io/en/latest/faq/metagenomes.html#) (after submitting them as bins). Some additional metadata is needed for a MAG submission.

### Contig- and Chromosome-MAG-Assemblies
A MAG assembly can be submitted either as a 'Contig Assembly' or a 'Chromosome Assembly'. Please consult [the ENA documentation for further information](https://ena-docs.readthedocs.io/en/latest/submit/assembly/metagenome/mag.html#stage-2-prepare-the-files). You will need to provide additional data for a Chromosome Assembly submission (see the [MAG metadata](#mag-metadata) section).

### MAG metadata
If you are submitting MAGs, you need to provide a .tsv file and specify it in the `MAGS_METADATA_FILE` field of your config file. The file needs to specifiy the columns `Bin_id`, `Sample_id`, `Quality_category`, `Flatfile_path` and `Unlocalised_path`. An example of such a file can be found in `./examples/data/mags/mags_metadata.tsv`.
Depending on your submission, not all columns have to be filled out.
- `Bin_id`: Identifier of the bin. Has to be identical to the identifier used in the name of the fasta file, the taxonomy .tsv files etc.
- `Quality_category`: 'finished', 'high' or 'medium' as defined by ENA [here](https://ena-docs.readthedocs.io/en/latest/faq/metagenomes.html) (note the requirements regarding RNA sequences for the 'high' and 'finished' categories).
- `Flatfile_path`: For chromosome assemblies only. Either a .FASTA file or an [EMBL-Flatfile](https://ena-docs.readthedocs.io/en/latest/submit/fileprep/flat-file-example.html) can be [used for MAG submission](https://ena-docs.readthedocs.io/en/latest/submit/fileprep/assembly.html#flat-file). If you leave the field empty, the .FASTA file of the corresponding bin will be used. If you want to provide annotation data, you need to provide a path to a flatfile. [EMBLmyGFF3](https://github.com/NBISweden/EMBLmyGFF3) provides a convenient way to create flatfiles based on your annotation data.
- `Unlocalised_path`: For chromosome assemblies only. Optional. [Path to a .txt file containing the unlocalised contigs of the bin](https://ena-docs.readthedocs.io/en/latest/submit/fileprep/assembly.html#unlocalised-list-file).

Using the table below, MAG `m1` will be submitted as a medium quality contig assembly without annotation. `m2` will be submitted as a high quality contig assembly and include annotation. MAG `m3` will be submitted as a finished chromosome assembly, including annotation. 
|Bin_id|Quality_category|Flatfile_path|Chromosomes_path|Unlocalised_path|
|---|---|---|---|---|
|m1|medium||||
|m2|high|/path/to/m2_flatfile.tsv|||
|m3|finished|/path/to/m3_flatfile.tsv|/path/to/m3_chromosome.txt|/path/to/m3_unlocalised.txt|

## Preventing Process Interruption
A submission can take several hours to complete. We recommend using [nohup](https://en.wikipedia.org/wiki/Nohup), [tmux](https://github.com/tmux/tmux/wiki) or something similar to prevent the process from being interrupted. 

# Taxonomy Assignment
Assemblies and bins need a valid NCBI taxonomy (scientific name and taxonomic identifier) for submission. If you did taxonomic annotation of bins based on [GTDB](https://gtdb.ecogenomic.org/), you can use the `gtdb_to_ncbi_majority_vote.py` script of the [GTDB-Toolkit](https://github.com/Ecogenomics/GTDBTk) to translate your results to NCBI taxonomy.

You can provide tables with NCBI taxonomy information for each bin (see `./tests/bacteria_taxonomy.tsv` for an example - the output of `gtdb_to_ncbi_majority_vote.py` has the correct format already). submg will use ENAs [suggest-for-submission-sendpoint](https://ena-docs.readthedocs.io/en/latest/retrieval/programmatic-access/taxon-api.html) to derive taxids that follow the [rules for bin taxonomy](https://ena-docs.readthedocs.io/en/latest/faq/taxonomy.html).

Either in addition to those files, or as an alternative you can provide a `MANUAL_TAXONOMY` table. This should specify the correct taxids and scientific names for bins. An example of such a document can be found in `./examples/data/taxonomy/manual_taxonomy_3bins.tsv`. If a bin is present in this document, the taxonomic data from the NCBI taxonomy tables will be ignored.

In some cases submg will be unable to assign a valid taxonomy to a bin. The submission will be aborted and you will be informed which bins are causing problems. In such cases you have to determine the correct scientific name and taxid for the bin and specify it in the `MANUAL_TAXONOMY` field of your config file. Sometimes the reason for a failed taxonomic assignment is that no proper taxid exists yet. You can [create a taxon request](https://ena-docs.readthedocs.io/en/latest/faq/taxonomy_requests.html) in the ENA Webin Portal to register the taxon.

## NCBI Taxonomy File
This file contains the NCBI taxonomy for bins. You can provide multiple taxonomy files covering different bins. If you created it with `gtdb_to_ncbi_majority_vote.py` of the [GTDB-Toolkit](https://github.com/Ecogenomics/GTDBTk) it will have the following, compatible format already. Alternatively, provide a .tsv file with the columns 'Bin_id' and 'NCBI_taxonomy'. The string in the 'NCBI_taxonomy' column has to adhere to the format shown below. Taxonomic ranks are separated by semicolons. On each rank, a letter indicating the rank is followed by two underscores and the classification at that rank. The ranks have to be in the order 'domain', 'phylum', 'class', 'order', 'family', 'genus', 'species'. If a classification at a certain rank is unavailable, the rank itself still needs to be present in the string (e.g. "s__").

|Bin_id|NCBI_taxonomy|
|---|---|
|bin2|d__Archaea;p__Euryarchaeota;c__Methanomicrobia;o__Methanomicrobiales;f__Methanomicrobiaceae;g__;s__|

## Manual Taxonomy File
In cases where submg is unable to assign a valid taxonomy based on the NCBI taxonomy file, you can provide taxonomies for certain bins here manually. The table matches each 'Bin_id' to a 'Scientific_name' and a 'Tax_id'. Taxonomy information for the bins can be split between the NCBI Taxonomy File and this. If a bin is present in this document, the taxonomic data from the NCBI taxonomy tables will be ignored.
|Bin_id|Scientific_name|Tax_id|
|---|---|---|
|bin3|uncultured Paracoccus sp.|189685|

ENA provides a [guideline for choosing taxonomy](https://ena-docs.readthedocs.io/en/latest/faq/taxonomy.html). You can query ENAs [suggest-for-submission-endpoint](https://ena-docs.readthedocs.io/en/latest/retrieval/programmatic-access/taxon-api.html) to find the correct taxid for a bin programmatically or directly through the browser (e.g. by navigating to https://www.ebi.ac.uk/ena/taxonomy/rest/suggest-for-submission/escherichia).

# Dereplication
If your bins are the result of dereplicating data from a single assembly you can use submg as described above. If your bins are the result of dereplicating data from multiple different assemblies, you need to split them based on which assembly they belong to. You then run submg seperately for each assembly (together with the corresponding set of bins).

# Bin Contamination above 100 percent
When calculating completeness and contamination of a bin with tools like [CheckM](https://github.com/Ecogenomics/CheckM), contamination values above 100% can occur. [Usually, this is not an error](https://github.com/Ecogenomics/CheckM/issues/107). However, the ENA API will refuse to accept bins with contamination values above 100%. This issue is unrelated to submg, but to avoid partial submissions submg will refuse to work if such a bin is present in the dataset. If you have bins with contamination values above 100% you can either leave them out by removing them from your dataset or manually set the contamination value to 100% in the `BINS_QUALITY_FILE` file you provide to submg.

# Support
submg is being actively developed. Please use the github [issue tracker](https://github.com/ttubb/submg/issues) to report problems. A [discussions page](https://github.com/ttubb/submg/discussions) is available for questions, comments and suggestions. 
