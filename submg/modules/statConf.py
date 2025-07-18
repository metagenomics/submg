from dataclasses import dataclass, field

@dataclass
class staticConfig:
    submg_version: str = '1.0.2'
    java_version: str = '17'
    webin_cli_version: str = '8.1.0'
    ena_dropbox_url: str = 'https://www.ebi.ac.uk/ena/submit/drop-box/submit/'
    ena_test_dropbox_url: str = 'https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/'
    ena_search_url: str = 'https://www.ebi.ac.uk/ena/portal/api/search'
    ena_test_search_url: str = 'https://wwwdev.ebi.ac.uk/ena/portal/api/search'
    sequence_assembly_type: str = "primary metagenome"
    zipped_fasta_extension: str = ".fna.gz"
    zipped_fastq_extension: str = ".fastq.gz"
    zipped_emblff_extension: str = ".embl.gz"
    fasta_extensions: str = '.fa;.fasta;.fna;.FA;.FASTA;.FNA'
    fastq_extensions: str = '.fq;.fastq;.FQ;.FASTQ'
    bam_extensions: str = '.bam;.BAM;'
    taxonomic_levels: str = 'species;genus;family;order;class;phylum;domain'
    molecule_types: str = 'genomic DNA;genomic RNA;viral cRNA;viral ssDNA;viral ssRNA;viral dsDNA;viral dsRNA'
    bin_assembly_quality: str = "Many fragments with little to no review of assembly other than reporting of standard assembly statistics."
    bin_investigation_type: str = 'metagenome-assembled genome'
    assembly_molecule_type: str = 'genomic DNA'
    max_contamination: int = 100
    max_assembly_name_length: int = 10
    valid_locations: str = "Afghanistan;Albania;Algeria;American Samoa;Andorra;Angola;Anguilla;Antarctica;Antigua and Barbuda;Arctic Ocean;Argentina;Armenia;Aruba;Ashmore and Cartier Islands;Atlantic Ocean;Australia;Austria;Azerbaijan;Bahamas;Bahrain;Baker Island;Baltic Sea;Bangladesh;Barbados;Bassas da India;Belarus;Belgium;Belize;Benin;Bermuda;Bhutan;Bolivia;Borneo;Bosnia and Herzegovina;Botswana;Bouvet Island;Brazil;British Virgin Islands;Brunei;Bulgaria;Burkina Faso;Burundi;Cambodia;Cameroon;Canada;Cape Verde;Cayman Islands;Central African Republic;Chad;Chile;China;Christmas Island;Clipperton Island;Cocos Islands;Colombia;Comoros;Cook Islands;Coral Sea Islands;Costa Rica;Cote d'Ivoire;Croatia;Cuba;Curacao;Cyprus;Czech Republic;Democratic Republic of the Congo;Denmark;Djibouti;Dominica;Dominican Republic;East Timor;Ecuador;Egypt;El Salvador;Equatorial Guinea;Eritrea;Estonia;Ethiopia;Europa Island;Falkland Islands (Islas Malvinas);Faroe Islands;Fiji;Finland;France;French Guiana;French Polynesia;French Southern and Antarctic Lands;Gabon;Gambia;Gaza Strip;Georgia;Germany;Ghana;Gibraltar;Glorioso Islands;Greece;Greenland;GrENAda;Guadeloupe;Guam;Guatemala;Guernsey;Guinea;Guinea-Bissau;Guyana;Haiti;Heard Island and McDonald Islands;Honduras;Hong Kong;Howland Island;Hungary;Iceland;India;Indian Ocean;Indonesia;Iran;Iraq;Ireland;Isle of Man;Israel;Italy;Jamaica;Jan Mayen;Japan;Jarvis Island;Jersey;Johnston Atoll;Jordan;Juan de Nova Island;Kazakhstan;Kenya;Kerguelen Archipelago;Kingman Reef;Kiribati;Kosovo;Kuwait;Kyrgyzstan;Laos;Latvia;Lebanon;Lesotho;Liberia;Libya;Liechtenstein;Lithuania;Luxembourg;Macau;Macedonia;Madagascar;Malawi;Malaysia;Maldives;Mali;Malta;Marshall Islands;Martinique;Mauritania;Mauritius;Mayotte;Mediterranean Sea;Mexico;Micronesia;Midway Islands;Moldova;Monaco;Mongolia;Montenegro;Montserrat;Morocco;Mozambique;Myanmar;Namibia;Nauru;Navassa Island;Nepal;Netherlands;New Caledonia;New Zealand;Nicaragua;Niger;Nigeria;Niue;Norfolk Island;Northern Mariana Islands;North Korea;North Sea;Norway;not applicable;not collected;not provided;Oman;Pacific Ocean;Pakistan;Palau;Palmyra Atoll;Panama;Papua New Guinea;Paracel Islands;Paraguay;Peru;Philippines;Pitcairn Islands;Poland;Portugal;Puerto Rico;Qatar;Republic of the Congo;restricted access;Reunion;Romania;Ross Sea;Russia;Rwanda;Saint HelENA;Saint Kitts and Nevis;Saint Lucia;Saint Pierre and Miquelon;Saint Vincent and the GrENAdines;Samoa;San Marino;Sao Tome and Principe;Saudi Arabia;Senegal;Serbia;Seychelles;Sierra Leone;Singapore;Sint Maarten;Slovakia;Slovenia;Solomon Islands;Somalia;South Africa;Southern Ocean;South Georgia and the South Sandwich Islands;South Korea;Spain;Spratly Islands;Sri Lanka;Sudan;Suriname;Svalbard;Swaziland;Sweden;Switzerland;Syria;Taiwan;Tajikistan;Tanzania;Tasman Sea;Thailand;Togo;Tokelau;Tonga;Trinidad and Tobago;Tromelin Island;Tunisia;Turkey;Turkmenistan;Turks and Caicos Islands;Tuvalu;Uganda;Ukraine;United Arab Emirates;United Kingdom;Uruguay;USA;Uzbekistan;Vanuatu;Venezuela;Viet Nam;Virgin Islands;Wake Island;Wallis and Futuna;West Bank;Western Sahara;Yemen;Zambia;Zimbabwe;missing: control sample;missing: data agreement established pre-2023;missing: endangered species;missing: human-identifiable;missing: lab stock;missing: sample group;missing: synthetic construct;missing: third party data;not applicable;not collected;not provided;restricted access"
    valid_sequencing_instruments: str = '454 GS;454 GS 20;454 GS FLX;454 GS FLX Titanium;454 GS FLX+;454 GS Junior;AB 310 Genetic Analyzer;AB 3130 Genetic Analyzer;AB 3130xL Genetic Analyzer;AB 3500 Genetic Analyzer;AB 3500xL Genetic Analyzer;AB 3730 Genetic Analyzer;AB 3730xL Genetic Analyzer;AB 5500 Genetic Analyzer;AB 5500xl Genetic Analyzer;AB 5500xl-W Genetic Analysis System;BGISEQ-50;BGISEQ-500;DNBSEQ-G400;DNBSEQ-G400 FAST;DNBSEQ-G50;DNBSEQ-T7;Element AVITI;GridION;Helicos HeliScope;HiSeq X Five;HiSeq X Ten;Illumina Genome Analyzer;Illumina Genome Analyzer II;Illumina Genome Analyzer IIx;Illumina HiScanSQ;Illumina HiSeq 1000;Illumina HiSeq 1500;Illumina HiSeq 2000;Illumina HiSeq 2500;Illumina HiSeq 3000;Illumina HiSeq 4000;Illumina HiSeq X;Illumina MiSeq;Illumina MiniSeq;Illumina NovaSeq 6000;Illumina NovaSeq X;Illumina iSeq 100;Ion GeneStudio S5;Ion GeneStudio S5 Plus;Ion GeneStudio S5 Prime;Ion Torrent Genexus;Ion Torrent PGM;Ion Torrent Proton;Ion Torrent S5;Ion Torrent S5 XL;MGISEQ-2000RS;MinION;NextSeq 1000;NextSeq 2000;NextSeq 500;NextSeq 550;PacBio RS;PacBio RS II;PromethION;Sequel;Sequel II;Sequel IIe;UG 100;unspecified'
    valid_sequencing_platforms: str = "BGISEQ;CAPILLARY;DNBSEQ;ELEMENT;HELICOS;ILLUMINA;ION_TORRENT;LS454;OXFORD_NANOPORE;PACBIO_SMRT;ULTIMA;ABI_SOLID;COMPLETE_GENOMICS"
    valid_library_sources: str = "GENOMIC;GENOMIC SINGLE CELL;TRANSCRIPTOMIC;TRANSCRIPTOMIC SINGLE CELL;METAGENOMIC;METATRANSCRIPTOMIC;SYNTHETIC;VIRAL RNA;OTHER"
    valid_library_strategies: str = "WGS;WGA;WXS;RNA-Seq;ssRNA-seq;miRNA-Seq;ncRNA-Seq;FL-cDNA;EST;Hi-C;ATAC-seq;WCS;RAD-Seq;CLONE;POOLCLONE;AMPLICON;CLONEEND;FINISHING;ChIP-Seq;MNase-Seq;Ribo-Seq;DNase-Hypersensitivity;Bisulfite-Seq;CTS;MRE-Seq;MeDIP-Seq;MBD-Seq;Tn-Seq;VALIDATION;FAIRE-seq;SELEX;RIP-Seq;ChIA-PET;Synthetic-Long-Read;Targeted-Capture;Tethered Chromatin Conformation Capture;OTHER"
    mag_assembly_quality_levels = "Many fragments with little to no review of assembly other than reporting of standard assembly statistics.;Single contiguous sequence without gaps or ambiguities with a consensus error rate equivalent to Q50 or better.;Multiple fragments where gaps span repetitive regions. Presence of the 23S, 16S and 5S rRNA genes and at least 18 tRNAs."
    webin_analysis_accession_line: str = 'The following analysis accession was assigned to the submission'
    webin_run_accessions_line: str = 'The following run accession was assigned to the submission'
    mag_metadata_columns: str = 'Bin_id;Quality_category;Flatfile_path;Unlocalised_path'
    ncbi_taxonomy_columns: str = 'Bin_id;NCBI_taxonomy'
    manual_taxonomy_columns: str = 'Bin_id;Scientific_name;Tax_id'
    gtdb_majority_vote_columns: str = 'Genome ID;GTDB classification;Majority vote NCBI classification'
    bin_coverage_columns: str = 'Bin_id;Coverage'
    bin_quality_columns = 'Bin Id;Completeness;Contamination'
    mag_qstring_finished: str = 'Single contiguous sequence without gaps or ambiguities with a consensus error rate equivalent to Q50 or better.'
    mag_qstring_high: str = 'Multiple fragments where gaps span repetitive regions. Presence of the 23S, 16S and 5S rRNA genes and at least 18 tRNAs.'
    mag_qstring_medium: str = 'Many fragments with little to no review of assembly other than reporting of standard assembly statistics.'
    max_assembly_name_length: int = 50 - len('webin-genome-' + '_SAMEA________')
    timestamp_length: int = 4
    ena_rest_rate_limit: int = 50 # requests per second
    submission_modes_message: str = """
        The following modes of submission are supported:

        Samples + Reads + Assembly + Bins + MAGs
        Samples + Reads + Assembly + Bins
        Samples + Reads + Assembly
        Samples + Reads
        Samples
                  Reads
                  Reads + Assembly + Bins + MAGs
                  Reads + Assembly + Bins
                  Reads + Assembly
                          Assembly + Bins + MAGs
                          Assembly + Bins
                          Assembly
                                     Bins + MAGs
                                     Bins
                                            MAGs
        
        Submitting single and paired reads at the same time works.
    """

YAMLCOMMENTS = {
    'STUDY': 'The accession of your study (which has to already exist in ENA).',
    'PROJECT_NAME': 'Name of the project within which the sequencing was organized.',
    'TITLE': 'A unique title for your sample.',
    'METAGENOME_SCIENTIFIC_NAME': "Taxonomic identifier of the metagenome. Check the ENA metagenome taxonomy tree to find a taxonomy ID and species name fitting your sample.",
    'METAGENOME_TAXID': "Taxonomic identifier of the assembly. Must match SPECIES_SCIENTIFIC_NAME.",
    'SEQUENCING_PLATFORMS': "One of https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#platform",
    'NEW_SAMPLES': "These samples will be created in ENA according to the data entered below. Your assembly MUST BE BASED ON ALL OF THESE.",
    'collection date': "Any ISO compliant time. Can be truncated from the right (e.g. '2023-12-27T16:07' or '2023-12').",
    'geographic location (country and/or sea)': 'See ENA checklists (e.g. https://www.ebi.ac.uk/ena/browser/view/ERC000011) for valid values.',
    'SAMPLE_ACCESSIONS': "These samples exist in ENA. Your assembly is based on them.",
    'ADDITIONAL_SAMPLESHEET_FIELDS': "You can add any additional fields of metadata to the samplesheet. They are recorded as pairs of keyword and value. There are no restrictions on what data can go in here. Use commas to separate list items. It is recommended to check the ENA samplesheet which most closely matches your data to see recommended fields.",
    'ADDITIONAL_MANIFEST_FIELDS': "You can add additional fields (as key value pairs) to be written to the manifest. Be aware that only certain fields are allowed here, depending on the type of data you are submitting. Consult the ENA documentation for information on allowed fields.",
    'NAME': "Choose any unique name.",
    'SEQUENCING_INSTRUMENT': "One of https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#instrument",
    'LIBRARY_SOURCE': "One of https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#permitted-values-for-library-source",
    'LIBRARY_SELECTION': "One of https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#permitted-values-for-library-source",
    'LIBRARY_STRATEGY': "One of https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#permitted-values-for-library-strategy",
    'FASTQ_FILE': "Path to a fastq file.",
    'FASTQ1_FILE': "Path to a fastq file with forward reads.",
    'FASTQ2_FILE': "Path to a fastq file with reverse reads.",
    'RELATED_SAMPLE_TITLE': "The title of the sample that these reads originate from",
    'RELATED_SAMPLE_ACCESSION': "The accession of the sample that these reads originate from",
    'ASSEMBLY_NAME': "Choose a name, even if your assembly has been uploaded already. Will only be used for naming assembly and bins/MAGs.",
    'EXISTING_ASSEMBLY_ANALYSIS_ACCESSION': "The accession of the assembly analysis that all bins/MAGs originate from",
    'EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION': "The accession of the virtual sample of the co-assembly which all bins/MAGs originate from",
    'ASSEMBLY_SOFTWARE': "Software used to generate the assembly.",
    'ISOLATION_SOURCE': "Describe where your sample was taken from.",
    'FASTA_FILE': "Path to a fasta file.",
    'geographic location (latitude)': "Use WGS84. For more information consult appropriate an ENA samplesheet template (e.g. https://www.ebi.ac.uk/ena/browser/view/ERC000050)",
    'geographic location (longitude)': "Use WGS84. For more information consult appropriate an ENA samplesheet template (e.g. https://www.ebi.ac.uk/ena/browser/view/ERC000050)",
    'broad-scale environmental context': "For more information consult appropriate an ENA samplesheet template (e.g. https://www.ebi.ac.uk/ena/browser/view/ERC000050)",
    'local environmental context': "For more information consult an appropriate ENA samplesheet template (e.g. https://www.ebi.ac.uk/ena/browser/view/ERC000050)",
    'environmental medium': "Pipe separated! For more information consult an ENA samplesheet template (e.g. https://www.ebi.ac.uk/ena/browser/view/ERC000050) and https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS",
    'RUN_ACCESSIONS': "Sequencing runs that were used to generate the assembly",
    'BINS_DIRECTORY': "Directory containing the fasta files of all bins/MAGs",
    'COMPLETENESS_SOFTWARE': "Software used to calculate completeness",
    'QUALITY_FILE': "tsv file containing quality values of each bin. Header must include 'Bin_id', 'Completeness', 'Contamination'. A CheckM output table will work here.",
    'NCBI_TAXONOMY_FILES' :"A list of files with NCBI taxonomy information about the bins. Consult the README to see how they should be structured.",
    'MANUAL_TAXONOMY_FILE': "Optional field, intended for bins not covered in NCBI_TAXONOMY_FILE. Scientific names and taxids for bins. See example file for the structure. Columns must be 'Bin_id', 'Tax_id' and 'Scientific_name'. Consult the README for more information.",
    'BINNING_SOFTWARE': "Name of the software that was used for taxonomic binning.",
    'binning parameters': "Parameters used for taxonomic binning. For more information consult an appropriate ENA samplesheet template (e.g. https://www.ebi.ac.uk/ena/browser/view/ERC000047)",
    'taxonomic identity marker': "For more information consult an appropriate ENA samplesheet template (e.g. https://www.ebi.ac.uk/ena/browser/view/ERC000047)",
    'BAM_FILES': "The reads from your experiment mapped back to the assembly",
    'COVERAGE_VALUE': "Read coverage of the assembly.",
    'COVERAGE_FILE': ".tsv file containing the coverage values of each bin. Columns must be 'Bin_id' and 'Coverage'.",
    'INSERT_SIZE': "Insert size of the paired-end reads (https://www.ebi.ac.uk/fg/annotare/help/seq_lib_spec.html)",
    'MAG_METADATA_FILE': "A .tsv specifying 'Bin_id', 'Sample_id', 'Quality_category', 'Flatfile_path', 'Chromosomes_path' and 'Unlocalised_path' for all MAGs. See README for more details.",
    'MIN_COMPLETENESS': "Bins with smaller completeness value will be discarded (in percent, 0-100). Remove this row to ignore bin completeness.",
    'MAX_CONTAMINATION': "Bins with larger contamination value will be discarded (in percent, 0-100). Remove this row to ignore bin contamination (>100% contamination bins will still be discarded).",
    'submission_outline': "This configuration form was created to submit the items listed below."
}

YAMLEXAMPLES = {
    'STUDY': '\"PRJEB71644\"',
    'PROJECT_NAME': '\"AgRFex 2 Biogas Survey\"',
    'TITLE': '\"Bioreactor_2_sample\"',
    'METAGENOME_SCIENTIFIC_NAME': '\"biogas fermenter metagenome\"',
    'METAGENOME_TAXID': '\"718289\"',
    'SEQUENCING_PLATFORMS': '[\"ILLUMINA\",\"OXFORD_NANOPORE\"]',
    'collection date': '\"2023-03\"',
    'geographic location (country and/or sea)': '\"Germany\"',
    'SAMPLE_ACCESSIONS': '[\"ERS15898933\",\"ERS15898932\"]',
    'NAME': '\"Bioreactor_2_replicate_1\"',
    'SEQUENCING_INSTRUMENT': '[\"Illumina HiSeq 1500\", \"GridION\"]',
    'LIBRARY_SOURCE': '\"GENOMIC\"',
    'LIBRARY_SELECTION': '\"RANDOM\"',
    'LIBRARY_STRATEGY': '\"WGS\"',
    'FASTQ_FILE': '\"/mnt/data/reads.fastq.gz\"',
    'FASTQ1_FILE': '\"/mnt/data/reads_R1.fastq.gz\"',
    'FASTQ2_FILE': '\"/mnt/data/reads_R2.fastq.gz\"',
    'RELATED_SAMPLE_TITLE': '\"Bioreactor_2_sample\"',
    'RELATED_SAMPLE_ACCESSION': '\"ERS15898933\"',
    'ASSEMBLY_NAME': '\"Swiss biogas digester metagenome\"',
    'EXISTING_ASSEMBLY_ANALYSIS_ACCESSION': '\"GCA_012552665\"',
    'EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION': '\"ERZ21942150\"',
    'ASSEMBLY_SOFTWARE': '\"MEGAHIT\"',
    'ISOLATION_SOURCE': '\"biogas plant anaerobic digester\"',
    'FASTA_FILE': '\"/mnt/data/assembly.fasta.gz\"',
    'geographic location (latitude)': '\"41.85\"',
    'geographic location (longitude)': '\"87.65\"',
    'broad-scale environmental context': '\"tropical biome\"',
    'local environmental context': '\"tropical marine upwelling biome\"',
    'environmental medium': '\"grass silage|animal waste material|anoxic water\"',
    'RUN_ACCESSIONS': '[\"ERR11585864\",\"ERR11584979\",\"ERR11584976\"]',
    'BINS_DIRECTORY': '\"/mnt/data/bins\"',
    'COMPLETENESS_SOFTWARE': '\"CheckM\"',
    'QUALITY_FILE': '\"/mnt/data/checkm_quality.tsv\"',
    'NCBI_TAXONOMY_FILES': '[\"/mnt/data/bacteria_tax.tsv\",\"/mnt/data/archaea_tax.tsv\"]',
    'MANUAL_TAXONOMY_FILE': '\"/mnt/data/manual_tax.tsv\"',
    'BINNING_SOFTWARE': '\"metabat2\"',
    'binning parameters': '\"default\"',
    'taxonomic identity marker': '\"multi marker approach\"',
    'MAG_METADATA_FILE': '\"/mnt/data/mag_data.tsv\"',
    'INSERT_SIZE': '\"300\"',
    'MIN_COMPLETENESS': '\"90\"',
    'MAX_CONTAMINATION': '\"5\"',
}

GUIEXAMPLES = {
    'STUDY': 'PRJEB71644',
    'PROJECT_NAME': 'AgRFex 2 Biogas Survey',
    'TITLE': 'Bioreactor_2_sample',
    'METAGENOME_SCIENTIFIC_NAME': 'biogas fermenter metagenome',
    'METAGENOME_TAXID': '718289',
    'SEQUENCING_PLATFORMS': 'ILLUMINA,OXFORD_NANOPORE',
    'collection date': '2023-03\n2024-12-27T16:07\n2012',
    'geographic location (country and/or sea)': 'Germany\nMediterranean Sea',
    'SAMPLE_ACCESSIONS': 'ERS15898933,ERS15898932',
    'NAME': 'Bioreactor_2_replicate_1',
    'SEQUENCING_INSTRUMENT': 'Illumina HiSeq 1500, GridION',
    'LIBRARY_SOURCE': 'GENOMIC',
    'LIBRARY_SELECTION': 'RANDOM',
    'LIBRARY_STRATEGY': 'WGS',
    'FASTQ_FILE': '/mnt/data/reads.fastq.gz',
    'FASTQ1_FILE': '/mnt/data/reads_R1.fastq.gz',
    'FASTQ2_FILE': '/mnt/data/reads_R2.fastq.gz',
    'RELATED_SAMPLE_TITLE': 'Bioreactor_2_sample',
    'RELATED_SAMPLE_ACCESSION': 'ERS15898933',
    'ASSEMBLY_NAME': 'Northern Germany biogas digester metagenome',
    'EXISTING_ASSEMBLY_ANALYSIS_ACCESSION': 'GCA_012552665',
    'EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION': 'ERZ21942150',
    'ASSEMBLY_SOFTWARE': 'MEGAHIT',
    'ISOLATION_SOURCE': 'biogas plant anaerobic digester',
    'FASTA_FILE': '/mnt/data/assembly.fasta.gz',
    'geographic location (latitude)': '41.85',
    'geographic location (longitude)': '87.65',
    'broad-scale environmental context': 'tropical biome',
    'local environmental context': 'tropical marine upwelling biome',
    'environmental medium': 'grass silage|animal waste material|anoxic water',
    'RUN_ACCESSIONS': 'ERR11585864,ERR11584979,ERR11584976',
    'BINS_DIRECTORY': '/mnt/data/bins',
    'COMPLETENESS_SOFTWARE': 'CheckM',
    'QUALITY_FILE': '/mnt/data/checkm_quality.tsv',
    'NCBI_TAXONOMY_FILES': '/mnt/data/bacteria_tax.tsv',
    'MANUAL_TAXONOMY_FILE': '/mnt/data/manual_tax.tsv',
    'BINNING_SOFTWARE': 'metabat2',
    'binning parameters': 'default',
    'taxonomic identity marker': 'multi-marker approach\n16S rRNA gene\nother',
    'MAG_METADATA_FILE': '/mnt/data/mag_data.tsv',
    'INSERT_SIZE': '300',
    'MIN_COMPLETENESS': '90',
    'MAX_CONTAMINATION': '5',
}

GUICOMMENTS = {
    'binning parameters': "Parameters used for taxonomic binning.",
    'taxonomic identity marker': "What information was used to assign taxonomy to the bins.",
    'COVERAGE_FILE': ".tsv file containing the coverage values of each bin. Columns must be 'Bin_id' and 'Coverage'. Consult the manual for more information.",
    'QUALITY_FILE': "tsv file containing quality values of each bin. Header must include 'Bin_id', 'Completeness', 'Contamination'. A CheckM output table will work here. Consult the manual for further details on the format.",
    'MAG_METADATA_FILE': "A .tsv specifying 'Bin_id', 'Sample_id', 'Quality_category', 'Flatfile_path', 'Chromosomes_path' and 'Unlocalised_path' for all MAGs. Consult the manual for more details.",
    'NCBI_TAXONOMY_FILES' :"A list of files with NCBI taxonomy information about the bins. Consult the manual to see how the files should be structured.",
    'MANUAL_TAXONOMY_FILE': "Scientific names and taxids for bins. See example file for the structure. Columns must be 'Bin_id', 'Tax_id' and 'Scientific_name'. Consult the manual for more information.",
    'BAM_FILES': "The reads from your experiment mapped back to the assembly. Pick all the BAM files that you have, one after another.",
    'SEQUENCING_PLATFORMS': "A comma-separated list of all sequencing platforms used. The link below specifies valid names for sequencing platforms.",
    'SEQUENCING_INSTRUMENT': "A comma-separated list of all sequencing instruments used. The link below specifies valid names for sequencing instruments.",
    'LIBRARY_SOURCE': "The source of the metagenomic library. The link below specifies valid values.",
    'LIBRARY_SELECTION': "The method used to select the DNA for sequencing. The link below specifies valid values.",
    'LIBRARY_STRATEGY': "The sequencing library strategy used. The link below specifies valid values.",
    'geographic location (country and/or sea)': 'The geographic location where the sample was taken. For example a specific country or sea. See ENA checklists (example link below) for valid values.',
    'geographic location (latitude)': "Latitude of sampling location. Use World Geodetic System (WGS84) for coodrinates.",
    'geographic location (longitude)': "Longitude of sampling location. Use World Geodetic System (WGS84) for coodrinates.",
    'broad-scale environmental context': "Environmental context of your sample. It is recommended to use ENVO terms (see link below)",
    'local environmental context': "Environmental context of your sample. It is recommended to use ENVO terms (see link below)",
    'environmental medium': "Environmental medium of your sample. It is recommended to use ENVO terms (see link below)",
}

GUILINKS = {
    'METAGENOME_SCIENTIFIC_NAME': {'ENA Taxonomy Tree': 'https://www.ebi.ac.uk/ena/browser/view/408169?show=tax-tree'},
    'METAGENOME_TAXID': {'ENA Taxonomy Tree': 'https://www.ebi.ac.uk/ena/browser/view/408169?show=tax-tree'},
    'SEQUENCING_PLATFORMS': {'Platform List': 'https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#platform'},
    'SEQUENCING_INSTRUMENT': {'Instrument List': 'https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#instrument'},
    'LIBRARY_SOURCE': {'Library Source List': 'https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#permitted-values-for-library-source'},
    'LIBRARY_SELECTION': {'Library Selection List': 'https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#permitted-values-for-library-source'},
    'LIBRARY_STRATEGY': {'Library Strategy List': 'https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#permitted-values-for-library-strategy'},
    'geographic location (country and/or sea)': {'Checklist Example': 'https://www.ebi.ac.uk/ena/browser/view/ERC000050'},
    'broad-scale environmental context': {
        'Using ENVO with MIxS': 'https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS',
        'Checklist Example': 'https://www.ebi.ac.uk/ena/browser/view/ERC000050'},
    'local environmental context': {
        'Using ENVO with MIxS': 'https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS',
        'Checklist Example': 'https://www.ebi.ac.uk/ena/browser/view/ERC000050'},
    'environmental medium': {
        'Using ENVO with MIxS': 'https://github.com/EnvironmentOntology/envo/wiki/Using-ENVO-with-MIxS',
        'Checklist Example': 'https://www.ebi.ac.uk/ena/browser/view/ERC000050'},
    'binning parameters': {'Checklist Example': 'https://www.ebi.ac.uk/ena/browser/view/ERC000047'},
    'INSERT_SIZE': {'About Insert Sizes': 'https://www.ebi.ac.uk/fg/annotare/help/seq_lib_spec.html'},
    'ADDITIONAL_SAMPLESHEET_FIELDS': {'Checklist Example': 'https://www.ebi.ac.uk/ena/browser/view/ERC000047'},
    'ADDITIONAL_MANIFEST_FIELDS': {'Fields Allowed in Assembly Manifest': 'https://ena-docs.readthedocs.io/en/latest/submit/assembly/genome.html#manifest-files',
                                   'Fields Allowed in Reads Manifest': 'https://ena-docs.readthedocs.io/en/latest/submit/reads/webin-cli.html#manifest-file'},
}

GUI_STATIC_ADDITIONAL_FIELDS = [
    'geographic location (latitude)',
    'geographic location (longitude)',
    'broad-scale environmental context',
    'local environmental context',
    'environmental medium',
    'binning parameters',
    'taxonomic identity marker',
]

YAML_PRETTYNAMES = {
    'STUDY': 'Study Accession',
    'PROJECT_NAME': 'Project Name',
    'TITLE': 'Sample Title',
    'METAGENOME_SCIENTIFIC_NAME': "Metagenome Scientific Name",
    'METAGENOME_TAXID': "Metagenome Taxonomic ID",
    'SEQUENCING_PLATFORMS': "Sequencing Platforms",
    'SINGLE_READS': "Unpaired Reads",
    'PAIRED_END_READS': "Paired Reads",
    'ASSEMBLY': "Metagenome Assembly",
    'BINS': "Binned Contigs",
    'MAGS': "Metagenome-Assembled Genomes",
    'NEW_SAMPLES': "New Samples",
    'collection date': "Collection Date",
    'geographic location (country and/or sea)': "Geog. Location (Country/Sea)",
    'SAMPLE_ACCESSIONS': "Sample Accessions",
    'ADDITIONAL_SAMPLESHEET_FIELDS': "Additional Samplesheet Fields",
    'ADDITIONAL_MANIFEST_FIELDS': "Additional Manifest Fields",
    'NAME': "Name",
    'SEQUENCING_INSTRUMENT': "Sequencing Instrument",
    'LIBRARY_SOURCE': "Library Source",
    'LIBRARY_SELECTION': "Library Selection",
    'LIBRARY_STRATEGY': "Library Strategy",
    'FASTQ_FILE': "FASTQ File",
    'FASTQ1_FILE': "FASTQ File (Forward Reads)",
    'FASTQ2_FILE': "FASTQ File (Reverse Reads)",
    'RELATED_SAMPLE_TITLE': "Related Sample Title",
    'RELATED_SAMPLE_ACCESSION': "Related Sample Accession",
    'ASSEMBLY_NAME': "Assembly Name",
    'EXISTING_ASSEMBLY_ANALYSIS_ACCESSION': "Existing Assembly Analysis Accession",
    'EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION': "Existing Co-Assembly Sample Accession",
    'ASSEMBLY_SOFTWARE': "Assembly Software",
    'ISOLATION_SOURCE': "Isolation Source",
    'FASTA_FILE': "FASTA File",
    'geographic location (latitude)': "Geographic Location (Latitude)",
    'geographic location (longitude)': "Geographic Location (Longitude)",
    'broad-scale environmental context': "Broad-Scale Environmental Context",
    'local environmental context': "Local Environmental Context",
    'environmental medium': "Environmental Medium",
    'RUN_ACCESSIONS': "Run Accessions",
    'BINS_DIRECTORY': "Bins Directory",
    'COMPLETENESS_SOFTWARE': "Completeness Software",
    'QUALITY_FILE': "Quality File",
    'NCBI_TAXONOMY_FILES': "NCBI Taxonomy Files",
    'MANUAL_TAXONOMY_FILE': "Manual Taxonomy File",
    'BINNING_SOFTWARE': "Binning Software",
    'binning parameters': "Binning Parameters",
    'taxonomic identity marker': "Taxonomic Identity Marker",
    'BAM_FILES': "BAM Files",
    'COVERAGE_VALUE': "Coverage Value",
    'COVERAGE_FILE': "Coverage File",
    'INSERT_SIZE': "Insert Size",
    'MAG_METADATA_FILE': "MAG Metadata File",
    'MIN_COMPLETENESS': "Minimum Completeness",
    'MAX_CONTAMINATION': "Maximum Contamination",
}

YAML_SINGLE_FILEKEYS = [
    "FASTQ_FILE",
    "FASTQ1_FILE", 
    "FASTQ2_FILE",
    "FASTA_FILE",
    "QUALITY_FILE",
    "MANUAL_TAXONOMY_FILE",
    "MAG_METADATA_FILE",
    "COVERAGE_FILE",
]

YAML_MULTI_FILEKEYS = [
    "NCBI_TAXONOMY_FILES",
    "BAM_FILES",
]

YAML_DIRKEYS = [
    "BINS_DIRECTORY",
]