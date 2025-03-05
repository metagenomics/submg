---
title: subMG Tutorial
---

<style>
  /* Hide the big header link that appears at the top */
  h1:first-of-type {
    display: none;
  }
</style>

# subMG Tutorial
This short tutorial will show you how to submit a toy metagenomics dataset using the command line interface of subMG.
A graphical user interface for subMG is available, but will not be covered in this tutorial.

In this tutorial, you will
- install subMG (comes with toy dataset)
- use subMG to create an empty configuration form for our toy dataset
- fill the form with all the (meta)data needed for submission
- use subMG to upload the toy dataset to the ENA development service.

**Important**: You will need an ENA account fort his tutorial. Newly created accounts cannot perform test submissions (submissions to the development service) right away. Submitting to the development service only works the after ENA development server's database has been synced, which occurs sometime after midnight GMT. If you plan on doing this tutorial and do not have an ENA account yet, you will need to create one and wait for the synchronization to happen before proceeding.

## Installation
Please refer to the [Installation](https://github.com/metagenomics/submg/#installation) section of the subMG README for instructions on how to install subMG on your operating system. For this tutorial, you need to install the CLI version of the tool. Make sure to activate your python virtual environment if you installed the tool in a venv.

## The ENA Development Service
ENA provides a development service to trial your submission before uploading your data to the production server. It is best practice to submit to the production service only after a test submission with identical parameters was successfully completed using the development service. For this tutorial, we will only be submitting data to the development service.

## ENA Account
An ENA account is required for data submission. If you do not have an account already, you can register at [the EBI website](https://www.ebi.ac.uk/ena/submit/webin).

**Important**: Newly created accounts cannot perform test submissions ([see above](#submg-tutorial)).

## Creating a Study
If a study is already registered with your ENA account, you can use it for this tutorial. Since we are only using the development service here, your existing study will not be affected.

If no study is available, you can create a new, non-permanent study with the development service. Navigate to the [Submissions Test Portal](https://wwwdev.ebi.ac.uk/ena/submit/webin) and log in. Click the yellow "Register Study" button. 

You will receive an accession number for your study. Write it down, as we will need it for the next steps.

## Planning Your Submission
As a first step of the submission process, you need to decide on what data you want submit. While it is possible to incrementally submit all data related to a study, submitting everything in one go saves a lot of work.
For this tutorial, we will be submitting:

- 2 Samples
- 2 Paired-End Sequencing Read Datasets
- 1 Metagenome Co-Assembly
- 4 Sets of Binned Contigs (=Metagenome Bins)

These items do not correspond to the actual submission steps, but subMG abstracts these details for us. Thus, it is sufficient to think about our submission in terms of the four bullet points shown above.

## Creating a Configuration Form
We provide the data & metadata of our study to subMG by filling out a configuration form. The `makecfg` command will create a minimal configuration form that is tailored to our submission. To specify what you wish to submit, run the following command:
```
submg-cli makecfg --submit-samples 2 --submit-paired-end-reads 2 --submit-assembly --submit-bins --known-coverage --outfile <path_to_your_new_config.yaml>
```
For samples and read sets it is neccessary to specify how many of these items you intend to submit. The empty form will be created at `<path_to_your_new_config.yaml>` specified by the `--outfile` argument.
The `--known-coverage` argument indicates that we have coverage information for our metagenome assembly and metagenomic bins already, so subMG will not have to derive this information from `.bam` files.

## Filling Your Configuration Form
Open the `yaml` form we just created with a text editor of your choice. Every field not starting with `ADDITIONAL` is _mandatory_, meaning it has to be filled out for ENA to accept your submission.
### Study
Enter the study identifier that we generated in the [Creating a Study](#creating-a-study) section.
```
STUDY: "PRJEB71644" # Do not copy, put in your own study accession instead!
```
### Metagenome Taxonomy
Enter a valid taxonomic identifier for your metagenome. You can browse the [NCBI metagenome taxonomies](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Undef&id=408169) to find a good fit. You will also need the corresponding taxid.
For our mock submission, we will be submitting an [ant fungus garden metagenome](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=797283&lvl=3&lin=f&keep=1&srchmode=1&unlock).
```
METAGENOME_SCIENTIFIC_NAME: "ant fungus garden metagenome"
METAGENOME_TAXID: "797283"   
```
### Sequencing Platforms
A list of sequencing platforms used in generating the read sets. ENA provides [a list of identifiers](https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#platform) for the different platforms. For our mock submission, the list only has a single entry.
```
SEQUENCING_PLATFORMS: ["ILLUMINA"] 
```

For a multi-item list, entries need to be comma-separated (e.g. `SEQUENCING_PLATFORMS: ["ILLUMINA", "OXFORD_NANOPORE"]`)

### Samples
We need to set metadata for our two biological samples. The sample title can be chosen freely, it just has to be unique for each sample in our study.

The collection date of the sample has to follow the ISO 8601 time format. While a granular timestamp like `2023-12-27T16:07` is valid, just putting `2023` will also work.

Furthermore, we need to specify a country or sea as a sampling location. You can refer to the options in the 'geographic location (country and/or sea)' field in ENA's [sample checklist 11](https://www.ebi.ac.uk/ena/browser/view/ERC000011) to see a list of all valid choices.

Under `ADDITIONAL_SAMPLESHEET_FIELDS` you can add any additonal information you'd have as key-value-pairs. This is not mandatory, but good practice.

For our toy dataset, we will specify two samples with different names and some additional metadata.
```
NEW_SAMPLES:
- TITLE: "antfung_s01"
  collection date: "2023-08"
  geographic location (country and/or sea): "Mexico"
  ADDITIONAL_SAMPLESHEET_FIELDS:
    sample storage temperature: "-80"
    oxygenation status of sample: "aerobic"
- TITLE: "antfung_s02"
  collection date: "2023-10"
  geographic location (country and/or sea): "Mexico"
  ADDITIONAL_SAMPLESHEET_FIELDS:
    sample storage temperature: "-80"
    oxygenation status of sample: "aerobic"
```

Make sure to use the correct number of spaces for indented items: 2 for the first level, 4 for the second level. Otherwise, your `.yaml` file won't be processed correctly.

### Read Datasets
Again, we need to choose a unique name for each read set. We also have to indicate, for each read set, which [sample](#samples) was the biological origin of the reads.

Afterwards, we need to provide information on how the reads were generated by listing the [sequencing instrument](https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#instrument), [library source](https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#permitted-values-for-library-source), [library selection](https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#permitted-values-for-library-selection) and [library strategy](https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#permitted-values-for-library-strategy). Only values from these lists are valid here.

Since we are submitting paired-end reads, we also need to specify the insert size (in bases).

We then need to enter the paths to the `.fastq` files with reads which we want to upload. subMG comes with suitable dummy files in the `examples/data/reads` directory. 

Again, we have the option to add additional metadata as key-value-pairs.

**Important**: When using windows, make sure you are using forward slashes (`/`) for all your file paths!

```
PAIRED_END_READS:                                 
- NAME: "idx00_dh_pe"
  SEQUENCING_INSTRUMENT: "Illumina HiSeq 1500"
  LIBRARY_SOURCE: "METAGENOMIC"
  LIBRARY_SELECTION: "RANDOM"
  LIBRARY_STRATEGY: "WGS"
  INSERT_SIZE: "300"
  FASTQ1_FILE: "<your_submg_directory>/examples/data/reads/fwd1.fastq"
  FASTQ2_FILE: "<your_submg_directory>/examples/data/reads/rev1.fastq"
  RELATED_SAMPLE_TITLE: "antfung_s01"
  ADDITIONAL_MANIFEST_FIELDS:
- NAME: "idx00_dh_pe2"
  SEQUENCING_INSTRUMENT: "Illumina MiSeq"
  LIBRARY_SOURCE: "METAGENOMIC"
  LIBRARY_SELECTION: "RANDOM"
  LIBRARY_STRATEGY: "WGS"
  INSERT_SIZE: "300"
  FASTQ1_FILE: "<your_submg_directory>/examples/data/reads/fwd2.fastq"
  FASTQ2_FILE: "<your_submg_directory>/examples/data/reads/rev2.fastq"
  RELATED_SAMPLE_TITLE: "antfung_s02"
  ADDITIONAL_MANIFEST_FIELDS:
```
### Co-Assembly
The assembly needs a name which just servers as an identifier within your project.

The assembly software field specifies which tool was used to generate the assembly (e.g. "MEGAHIT").

Isolation source describes the physical, environmental and/or local geographical source of the biological sample from which the sequence was derived. It doesn't have to adhere to a special format. Choose a succinct but informative term, like "rumen isolates from standard Pelleted ration-fed steer #67" 

The path to our assembly can be supplied in the fasta file field. The file may be gzipped. subMG comes with a small mock assembly file in the `examples/data` directory.

Collection date is an ISO 8601 entry (as explained in the [samples](#samples) section above). When you are submitting a co-assembly based on samples collected at different times, you can enter "not applicable".

See the [samples](#samples) section regarding the 'geographic location (country and/or sea)' field. Should this be a co-assembly based on samples from different locations, you can enter "not applicable".

Since we chose the `--known-coverage` option in the beginning, we now have to provide a depth of coverage value for our assembly.

```
ASSEMBLY:                                         
  ASSEMBLY_NAME: 'myassembly'
  ASSEMBLY_SOFTWARE: 'metaSPAdes'
  ISOLATION_SOURCE: 'fungus garden in wild atta mexicana colony'
  FASTA_FILE: "<your_submg_directory>/examples/data/assembly.fasta"
  collection date: '2012-02'
  geographic location (country and/or sea): 'Mexico'
  COVERAGE_VALUE: 73.2
  ADDITIONAL_SAMPLESHEET_FIELDS:
  ADDITIONAL_MANIFEST_FIELDS: 
```

### Binned Contigs
We don't provide a list of individual files for binned contigs, but instead specify a directory. It is important that *every* file in this directory represents a set of binned contigs. subMG comes with a minimal example in the `examples/data/2bins` directory.

For binned contigs, it is mandatory to provide information about the quality of the resulting metagenomic bins. The completeness software field should indicate which software was used to compute this. Furthermore, we need to supply a `.tsv` table with quality information for all bins. It needs to contain the columns `Bin_id`, `Completeness` and `Contamination`. The bin ids have to correspond to the basenames of files in the binned contigs directory. [CheckM](https://github.com/Ecogenomics/CheckM) uses this format by default for the tabular output. For the tutorial we can use the file at `examples/data/checkm_quality_2bins.tsv`

We need to submit [valid taxonomic information](https://ena-docs.readthedocs.io/en/latest/faq/taxonomy.html) for our metagenomic bins. We can provide this information to subMG as a `.tsv` table with the columns 'Bin_id', 'Tax_id' and 'Scientific_name' in the `MANUAL_TAXONOMY_FILE` field. The easier option is usally to provide one ore more tables with NCBI taxonomy data in the `NCBI_TAXONOMY_FILES` field. The output of [GTDB-Tk's](https://github.com/Ecogenomics/GTDBTk) `gtdb_to_ncbi_majority_vote.py` script can be used here. subMG will then derive the correct taxonomy for submission automatically. For more information about the topic, consult the [Taxonomy section of the subMG README](https://github.com/metagenomics/submg/#taxonomy-assignment). For our toy dataset, we can use the two taxonomy files located at `examples/data/taxonomy/archaea_taxonomy.tsv` and `examples/data/taxonomy/bacteria_taxonomy.tsv`.

The software that was used for the binning of contigs needs to be named (e.g. "VAMB" or "maxbin2").

Since we chose the `--known-coverage` option instead of `--coverage-from-bam`, we need to supply a `.tsv` table with depth of coverage information for each metagenomic bin. This table has to contain the columns `Bin_id` and `Coverage`. A coverage table for our three mock bins is available at `examples/data/bin_coverage.tsv`.

```
BINS:
  BINS_DIRECTORY: "<your_submg_directory>/examples/data/2bins"
  COMPLETENESS_SOFTWARE: "CheckM"
  QUALITY_FILE: "<your_submg_directory>/examples/data/checkm_quality_2bins.tsv"
  NCBI_TAXONOMY_FILES: ["<your_submg_directory>/examples/data/taxonomy/archaea_taxonomy.tsv", "<your_submg_directory>/examples/data/taxonomy/bacteria_taxonomy.tsv"]
  MANUAL_TAXONOMY_FILE:
  BINNING_SOFTWARE: "metabat2"
  ADDITIONAL_SAMPLESHEET_FIELDS:
  ADDITIONAL_MANIFEST_FIELDS:
  COVERAGE_FILE: "<your_submg_directory>/examples/data/bin_coverage.tsv"
```

This was our last section and we are done filling out our config. Save the config file before continuing.

## Login Data
subMG requires our ENA credentials to submit data. You must set them as environment variables in your terminal session.

In the linux terminal:
```
export ENA_USER=your_ena_username
export ENA_PASSWORD=your_ena_password
```

In the windows command prompt (cmd):
```
set ENA_USER=your_ena_username
set ENA_PASSWORD=your_ena_password
```

## Starting Your Submission
You should have completely filled out your configuration form during the previous steps. For reference, the filled out form is shown [below](#completed-configuration-form).

For the submission, you will need two directories: One where subMG will stage all files prior to upload, and one where the tool will write logs. You can start the submission to the test server using the `submit` command. You will have to specify the aforementioned directories, the location of you configuration form and the types of items you'd like to submit.
```
submg-cli submit --config <path_to_your_config_form> --staging-dir <path_to_your_staging_directory> --logging-dir <path_to_your_logging_directory> --submit-samples --submit-reads --submit-assembly --submit-bins
```

Most likely you will receive an error because the accession of your study only exists on the development server. Add the `--skip-checks` flag to your command to circumvent this.
```
submg-cli submit --config <path_to_your_config_form> --staging-dir <path_to_your_staging_directory> --logging-dir <path_to_your_logging_directory> --submit-samples --submit-reads --submit-assembly --submit-bins --skip-checks
```

It is recommended to always submit to the test server before starting an actual submission. As such, submitting to the test server is the default behaviour in subMG. If you want to submit to the production service, add `--development-service 0` to your command.

## Completed Configuration Form
For the form below to work, you need to
- Insert the accession of your study
- Place the form in your `submg/examples` directory or replace all filepaths with absolute paths
- When using windows, make sure to use forward slashes (`/`) for all file paths
```
STUDY: "YOURSTUDY"
METAGENOME_SCIENTIFIC_NAME: "ant fungus garden metagenome"
METAGENOME_TAXID: "797283"   
NEW_SAMPLES:
- TITLE: 'antfung_s01'
  collection date: '2023-08'
  geographic location (country and/or sea): "Mexico"
  ADDITIONAL_SAMPLESHEET_FIELDS:
    sample storage temperature: "-80"
    oxygenation status of sample: "aerobic"
- TITLE: 'antfung_s02'
  collection date: '2023-10'
  geographic location (country and/or sea): "Mexico"
  ADDITIONAL_SAMPLESHEET_FIELDS:
    sample storage temperature: "-80"
    oxygenation status of sample: "aerobic"
PAIRED_END_READS:                                 
- NAME: "idx00_dh_pe"
  SEQUENCING_INSTRUMENT: "Illumina HiSeq 1500"
  LIBRARY_SOURCE: "METAGENOMIC"
  LIBRARY_SELECTION: "RANDOM"
  LIBRARY_STRATEGY: "WGS"
  INSERT_SIZE: "300"
  FASTQ1_FILE: "data/reads/fwd1.fastq"
  FASTQ2_FILE: "data/reads/rev1.fastq"
  RELATED_SAMPLE_TITLE: "antfung_s01"
  ADDITIONAL_MANIFEST_FIELDS:
- NAME: "idx00_dh_pe2"
  SEQUENCING_INSTRUMENT: "Illumina MiSeq"
  LIBRARY_SOURCE: "METAGENOMIC"
  LIBRARY_SELECTION: "RANDOM"
  LIBRARY_STRATEGY: "WGS"
  INSERT_SIZE: "300"
  FASTQ1_FILE: "data/reads/fwd2.fastq"
  FASTQ2_FILE: "data/reads/rev2.fastq"
  RELATED_SAMPLE_TITLE: "antfung_s02"
  ADDITIONAL_MANIFEST_FIELDS:
ASSEMBLY:                                         
  ASSEMBLY_NAME: 'myassembly'
  ASSEMBLY_SOFTWARE: 'metaSPAdes'
  ISOLATION_SOURCE: 'fungus garden in wild atta mexicana colony'
  FASTA_FILE: "data/assembly.fasta"
  collection date: '2012-02'
  geographic location (country and/or sea): 'Mexico'
  COVERAGE_VALUE: 73.2
  ADDITIONAL_SAMPLESHEET_FIELDS:
  ADDITIONAL_MANIFEST_FIELDS: 
BINS:
  BINS_DIRECTORY: "data/2bins"
  COMPLETENESS_SOFTWARE: "CheckM"
  QUALITY_FILE: "data/checkm_quality_2bins.tsv"
  NCBI_TAXONOMY_FILES: ["data/taxonomy/archaea_taxonomy.tsv", "data/taxonomy/bacteria_taxonomy.tsv"]
  MANUAL_TAXONOMY_FILE:
  BINNING_SOFTWARE: "metabat2"
  ADDITIONAL_SAMPLESHEET_FIELDS:
  ADDITIONAL_MANIFEST_FIELDS:
  COVERAGE_FILE: "data/bin_coverage.tsv"
```