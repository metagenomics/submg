from dataclasses import dataclass, field

@dataclass
class staticConfig:
    synum_version: str = '0.1.0'
    webin_cli_version: str = '6.7.2'
    #ena_dropbox_url: str = 'https://www.ebi.ac.uk/ena/submit/webin-v2/submit/'
    #ena_test_dropbox_url: str = 'https://wwwdev.ebi.ac.uk/ena/submit/webin-v2/submit/'
    ena_dropbox_url: str = 'https://www.ebi.ac.uk/ena/submit/drop-box/submit/'
    ena_test_dropbox_url: str = 'https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/'
    ena_search_url: str = 'https://www.ebi.ac.uk/ena/portal/api/search'
    sequence_assembly_type: str = "primary metagenome"
    zipped_fasta_extension: str = ".fna.gz"
    zipped_fastq_extension: str = ".fastq.gz"
    fasta_extensions: str = '.fa;.fasta;.fna;.FA;.FASTA;.FNA'
    bam_extensions: str = '.bam;.BAM;'
    taxonomic_levels: str = 'species;genus;family;order;class;phylum;kingdom'
    molecule_types: str = 'genomic DNA;genomic RNA;viral cRNA;viral ssDNA;viral ssRNA;viral dsDNA;viral dsRNA'
    bin_assembly_quality: str = "Many fragments with little to no review of assembly other than reporting of standard assembly statistics."
    bin_investigation_type: str = 'metagenome-assembled genome'
    assembly_molecule_type: str = 'genomic DNA'
    max_contamination: int = 100
    max_assembly_name_length: int = 10
    valid_locations: str = "Afghanistan;Albania;Algeria;American Samoa;Andorra;Angola;Anguilla;Antarctica;Antigua and Barbuda;Arctic Ocean;Argentina;Armenia;Aruba;Ashmore and Cartier Islands;Atlantic Ocean;Australia;Austria;Azerbaijan;Bahamas;Bahrain;Baker Island;Baltic Sea;Bangladesh;Barbados;Bassas da India;Belarus;Belgium;Belize;Benin;Bermuda;Bhutan;Bolivia;Borneo;Bosnia and Herzegovina;Botswana;Bouvet Island;Brazil;British Virgin Islands;Brunei;Bulgaria;Burkina Faso;Burundi;Cambodia;Cameroon;Canada;Cape Verde;Cayman Islands;Central African Republic;Chad;Chile;China;Christmas Island;Clipperton Island;Cocos Islands;Colombia;Comoros;Cook Islands;Coral Sea Islands;Costa Rica;Cote d'Ivoire;Croatia;Cuba;Curacao;Cyprus;Czech Republic;Democratic Republic of the Congo;Denmark;Djibouti;Dominica;Dominican Republic;East Timor;Ecuador;Egypt;El Salvador;Equatorial Guinea;Eritrea;Estonia;Ethiopia;Europa Island;Falkland Islands (Islas Malvinas);Faroe Islands;Fiji;Finland;France;French Guiana;French Polynesia;French Southern and Antarctic Lands;Gabon;Gambia;Gaza Strip;Georgia;Germany;Ghana;Gibraltar;Glorioso Islands;Greece;Greenland;GrENAda;Guadeloupe;Guam;Guatemala;Guernsey;Guinea;Guinea-Bissau;Guyana;Haiti;Heard Island and McDonald Islands;Honduras;Hong Kong;Howland Island;Hungary;Iceland;India;Indian Ocean;Indonesia;Iran;Iraq;Ireland;Isle of Man;Israel;Italy;Jamaica;Jan Mayen;Japan;Jarvis Island;Jersey;Johnston Atoll;Jordan;Juan de Nova Island;Kazakhstan;Kenya;Kerguelen Archipelago;Kingman Reef;Kiribati;Kosovo;Kuwait;Kyrgyzstan;Laos;Latvia;Lebanon;Lesotho;Liberia;Libya;Liechtenstein;Lithuania;Luxembourg;Macau;Macedonia;Madagascar;Malawi;Malaysia;Maldives;Mali;Malta;Marshall Islands;Martinique;Mauritania;Mauritius;Mayotte;Mediterranean Sea;Mexico;Micronesia;Midway Islands;Moldova;Monaco;Mongolia;Montenegro;Montserrat;Morocco;Mozambique;Myanmar;Namibia;Nauru;Navassa Island;Nepal;Netherlands;New Caledonia;New Zealand;Nicaragua;Niger;Nigeria;Niue;Norfolk Island;Northern Mariana Islands;North Korea;North Sea;Norway;not applicable;not collected;not provided;Oman;Pacific Ocean;Pakistan;Palau;Palmyra Atoll;Panama;Papua New Guinea;Paracel Islands;Paraguay;Peru;Philippines;Pitcairn Islands;Poland;Portugal;Puerto Rico;Qatar;Republic of the Congo;restricted access;Reunion;Romania;Ross Sea;Russia;Rwanda;Saint HelENA;Saint Kitts and Nevis;Saint Lucia;Saint Pierre and Miquelon;Saint Vincent and the GrENAdines;Samoa;San Marino;Sao Tome and Principe;Saudi Arabia;Senegal;Serbia;Seychelles;Sierra Leone;Singapore;Sint Maarten;Slovakia;Slovenia;Solomon Islands;Somalia;South Africa;Southern Ocean;South Georgia and the South Sandwich Islands;South Korea;Spain;Spratly Islands;Sri Lanka;Sudan;Suriname;Svalbard;Swaziland;Sweden;Switzerland;Syria;Taiwan;Tajikistan;Tanzania;Tasman Sea;Thailand;Togo;Tokelau;Tonga;Trinidad and Tobago;Tromelin Island;Tunisia;Turkey;Turkmenistan;Turks and Caicos Islands;Tuvalu;Uganda;Ukraine;United Arab Emirates;United Kingdom;Uruguay;USA;Uzbekistan;Vanuatu;Venezuela;Viet Nam;Virgin Islands;Wake Island;Wallis and Futuna;West Bank;Western Sahara;Yemen;Zambia;Zimbabwe"
    webin_analysis_accession_line: str = 'The following analysis accession was assigned to the submission'
    webin_run_accessions_line: str = 'The following run accession was assigned to the submission'