from dataclasses import dataclass, field

@dataclass
class staticConfig:
    synum_version: str = '0.1.0'
    webin_cli_version: str = '6.7.2'
    #ena_dropbox_url: str = 'https://www.ebi.ac.uk/ena/submit/webin-v2/submit/'
    #ena_test_dropbox_url: str = 'https://wwwdev.ebi.ac.uk/ena/submit/webin-v2/submit/'
    ena_dropbox_url: str = 'https://www.ebi.ac.uk/ena/submit/drop-box/submit/'
    ena_test_dropbox_url: str = 'https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/'
    co_assembly_checklist: str = "ERC000011"
    sequence_assembly_type: str = "primary metagenome"
    zipped_fasta_extension: str = ".fna.gz"
    fasta_extensions: str = '.fa;.fasta;.fna;.FA;.FASTA;.FNA'
    bam_extensions: str = '.bam;.BAM;'
    taxonomic_levels: str = 'species;genus;family;order;class;phylum;kingdom'
    molecule_types: str = 'genomic DNA;genomic RNA;viral cRNA;viral ssDNA;viral ssRNA;viral dsDNA;viral dsRNA'
    bin_assembly_quality: str = "Many fragments with little to no review of assembly other than reporting of standard assembly statistics."
    bin_investigation_type: str = 'metagenome-assembled genome'
    max_contamination: int = 100
    max_assembly_name_length: int = 10