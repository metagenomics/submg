import argparse
import os
import time
import traceback
import sys

from .modules import loggingC
from .modules import preflight
from .modules import utility
from .modules import webinDownload
from .modules import configGen 
from .modules import taxQuery
from .modules import enaSearching

from .modules.statConf import staticConfig
from .modules.utility import prepdir
from .modules.sampleSubmission import submit_samples
from .modules.readSubmission import submit_reads
from .modules.assemblySubmission import submit_assembly
from .modules.binSubmission import submit_bins, get_bin_quality
from .modules.magSubmission import submit_mags


def init_argparse():
    """
    Use argparse to parse command line arguments and return the arguments
    object.

    Returns:
        argparse.ArgumentParser: The arguments object.
    """
    submg_description = """Tool for submitting metagenome study data to the
                           European Nucleotide Archive (ENA). Environment
                           variables ENA_USER and ENA_PASSWORD must be set for
                           data upload."""

    parser = argparse.ArgumentParser(description=submg_description)
    parser.add_argument("-v", "--version",
                        action="version",
                        version=f"%(prog)s {staticConfig.submg_version}")
    
    subparsers = parser.add_subparsers(dest='mode')

    subparsers.add_parser('download_webin',
                          help='Download a compatible '
                          'version of the webin-cli .jar file')

    parser_submit = subparsers.add_parser('submit',
                                          help='Stage your data and submit it '
                                          'to either the ENA development or '
                                          'production server')
    parser_submit.add_argument("-x",
                               "--config",
                               required=True,
                               help="Path to the YAML file containing "
                               "metadata and filepaths. Mandatory")
    parser_submit.add_argument("-g",
                               "--staging_dir",
                               required=True,
                               help="Directory where files will be staged for "
                               "upload. Must be empty. May use up a lot of "
                               "disk space. Mandatory.")
    parser_submit.add_argument("-l", "--logging_dir",
                               required=True,
                               help="Directory where log files will be "
                               "stored. Must be empty. Mandatory.")
    parser_submit.add_argument("-y", "--verbosity",
                               type=int,
                               choices=[0, 1, 2],
                               default=1,
                               help="Control the amount of logging to stdout. "
                               "[default 1]")
    parser_submit.add_argument("-d",
                               "--development_service",
                               type=int,
                               choices=[0, 1],
                               default=1,
                               help="Make submissions to the ENA development "
                               "test server. [default 1/true]")
    parser_submit.add_argument("-i",
                               "--minitest",
                               action="store_true",
                               help="Run a minimal test submission using just "
                               "a fraction of your dataset. Intended for quick "
                               "troubleshooting. [default false]")
    parser_submit.add_argument("-t",
                               "--threads",
                               type=int,
                               default=4,
                               help="Number of threads used to process .bam "
                               "files. [default 4]")
    parser_submit.add_argument("--keep_depth_files",
                               action="store_true",
                               help="Do not delete depth files after running. "
                               "[default false]")
    parser_submit.add_argument("-r",
                               "--submit_reads",
                               action="store_true",
                               default=False,
                               help="Use if you want to submit reads.")
    parser_submit.add_argument("-s",
                               "--submit_samples",
                               action="store_true",
                               default=False,
                               help="Use if you want to submit (biological) "
                               "sample objects.")
    parser_submit.add_argument("-a",
                               "--submit_assembly",
                               action="store_true",
                               default=False,
                               help="Use if you want to submit one assembly. "
                               "To submit multiple assemblies, you need to "
                               "use the tool multiple times.")
    parser_submit.add_argument("-b",
                               "--submit_bins",
                               action="store_true",
                               default=False,
                               help="Use if you want to submit metagenome "
                               "bins (note that bins are different from MAGs "
                               "in the ENA definition).")
    parser_submit.add_argument("-m",
                               "--submit_mags",
                               action="store_true",
                               default=False,
                               help="Use if you want to submit "
                               "metagenome-assembled genomes (MAGs).")
    parser_submit.add_argument("--skip_checks",
                               action="store_true",
                               default=False,
                               help="Skip preflight checks. Use with caution.")
    parser_submit.add_argument("-z", "--timestamps",
                               type=int,
                               choices=[0, 1],
                               help="Add timestamps to the names of submitted "
                               "items. This prevents name clashes when "
                               "submitting the same data multiple times during "
                               "testing. Defaults to true when using the "
                               "development_service, defaults to false "
                               "otherwise.")

    parser_makecfg = subparsers.add_parser('makecfg',
                                           help='Create a .yml file '
                                           'containing the fields you need to '
                                           'fill out prior to submission')
    parser_makecfg.add_argument("-o",
                                "--outfile",
                                required=True,
                                help="Path to the empty config that will be "
                                "generated.")
    parser_makecfg.add_argument("-c",
                                "--no_comments",
                                action="store_true",
                                default=False,
                                help="Do not include field descriptions in "
                                "the config file.")
    parser_makecfg.add_argument("-s",
                                "--submit_samples",
                                type=int, default=0,
                                help="If you want to submit (biological) "
                                "sample objects, specify how many.")    
    parser_makecfg.add_argument("-rs",
                                "--submit_single_reads",
                                type=int,
                                default=0,
                                help="If you want to submit non-paired read "
                                "files, specify how many.")
    parser_makecfg.add_argument("-rp",
                                "--submit_paired_end_reads",
                                type=int,
                                default=0,
                                help="If you want to submit paired-end read "
                                "files, specify how many.")
    parser_makecfg.add_argument("-b",
                                "--submit_bins",
                                action="store_true",
                                default=False,
                                help="Use if you want to submit metagenome "
                                "bins (note that bins are different from MAGs "
                                "in the ENA definition).")
    parser_makecfg.add_argument("-m",
                                "--submit_mags",
                                action="store_true",
                                default=False,
                                help="Use if you want to submit "
                                "metagenome-assembled genomes (MAGs).")
    parser_makecfg.add_argument("-a",
                                "--submit_assembly",
                                action="store_true",
                                default=False,
                                help="Use if you want to submit one assembly. "
                                "To submit multiple assemblies, you need to "
                                "use the tool multiple times.")
    parser_makecfg.add_argument("-q",
                                "--bin_quality_cutoffs",
                                action="store_true",
                                default=False,
                                help="Include fields for bin quality cutoff "
                                "(contamination & completeness) in config.")

    coverage_group = parser_makecfg.add_mutually_exclusive_group(required=False)
    coverage_group.add_argument("--coverage_from_bam",
                                action="store_true",
                                help="Coverages will be calculated from a "
                                "list of .bam files that you provide. WARNING: "
                                "This does not work on windows systems.")
    coverage_group.add_argument("--known_coverage",
                                action="store_true",
                                help="Coverages are already known and you "
                                "provide them as a .bam file.")

    return parser


def download_webin():
    """
    Download the webin-cli .jar file.
    """
    toolVersion, webinCliVersion = webinDownload.versions()
    print(f">Versions: tool={toolVersion}, webin-cli={webinCliVersion}")
    print(">Checking Java installation...")
    webinDownload.check_java()
    webinDownload.download_webin_cli(webinCliVersion)


def makecfg_through_gui(outpath,
                        submit_samples,
                        submit_single_reads,
                        submit_paired_end_reads,
                        coverage_from_bam,
                        known_coverage,
                        submit_assembly,
                        submit_bins,
                        submit_mags,
                        quality_cutoffs):
    if coverage_from_bam and sys.platform == "win32":
        err = ("ERROR: The --coverage_from_bam option does not work on "
                "Windows systems.")
        loggingC.message(err, threshold=-1)
        exit(1)
        
    print("input arguments of makecfg_through_gui:")
    print("coverage from bam", coverage_from_bam)
    print("known coverage", known_coverage)
    configGen.make_config(outpath=outpath,
                          submit_samples=submit_samples,
                          submit_single_reads=submit_single_reads,
                          submit_paired_end_reads=submit_paired_end_reads,
                          coverage_from_bam=coverage_from_bam,
                          known_coverage=known_coverage,
                          submit_assembly=submit_assembly,
                          submit_bins=submit_bins,
                          submit_mags=submit_mags,
                          no_comments=False,
                          quality_cutoffs=quality_cutoffs)


def makecfg(args):
    """
    Create a .yml file containing the fields a user needs to fill in order to
    create a submission for their specific setup.

    Will exit with an error if the user tries to use --coverage_from_bam on a
    Windows system.
    """
    if args.coverage_from_bam and sys.platform == "win32":
        wrn = ("WARNING: The --coverage_from_bam option does not work on "
                "Windows systems!\n "
                "You can still create a config, but you will not be able to "
                "submit it using a Windows machine.\n\n")
        loggingC.message(wrn, threshold=-1)
        # Wait for 10 seconds to give the user time to read the message
        time.sleep(10)
        
    configGen.make_config(outpath=args.outfile,
                          submit_samples=args.submit_samples,
                          submit_single_reads=args.submit_single_reads,
                          submit_paired_end_reads=args.submit_paired_end_reads,
                          coverage_from_bam=args.coverage_from_bam,
                          known_coverage=args.known_coverage,
                          submit_assembly=args.submit_assembly,
                          submit_bins=args.submit_bins,
                          submit_mags=args.submit_mags,
                          no_comments=args.no_comments,
                          quality_cutoffs=args.bin_quality_cutoffs)
    

def submit_through_gui(config_path,
                       output_dir,
                       listener,
                       development_service,
                       verbosity,
                       submit_samples,
                       submit_reads,
                       submit_assembly,
                       submit_bins,
                       submit_mags,
                       username,
                       password):
    # Create timestamped logging and staging directories
    timestamp = utility.full_timestamp()
    logging_dir = os.path.join(output_dir, f"submg_logging_{timestamp}")
    staging_dir = os.path.join(output_dir, f"submg_staging_{timestamp}")

    # Create an args object to use with the submit() function
    args = argparse.Namespace()
    args.config = config_path
    args.staging_dir = staging_dir
    args.logging_dir = logging_dir
    args.verbosity = verbosity
    args.development_service = development_service
    args.skip_checks = False
    args.timestamps = 1
    args.threads = 4
    args.keep_depth_files = False
    args.submit_samples = submit_samples
    args.submit_reads = submit_reads
    args.submit_assembly = submit_assembly
    args.submit_bins = submit_bins
    args.submit_mags = submit_mags
    args.minitest = False

    # Set credentials
    utility.set_gui_credentials(username, password)

    # Initialize submission
    submit(args, listener)


def submit(args, listener=None):
    """
    Submit data to the ENA.

    Args:
        args (argparse.Namespace): The arguments object.
    """
    print("I AM RUNNING SUBMIT!")
    loggingC.set_up_logging(args.logging_dir, args.verbosity, listener)
    print("I HAVE SET UP LOGGING!")
    
    if args.timestamps or (args.timestamps is None and args.development_service):
        utility.set_up_timestamps(vars(args))

    if args.minitest and not args.development_service:
        loggingC.message("ERROR: The --minitest mode cannot be used for a submission to the ENA production server.",
                         threshold=-1)
        
    print("TRY BLOCK")
    try:
        sver = staticConfig.submg_version
        wver = staticConfig.webin_cli_version
        loggingC.message(f">Running submg {sver} with webin-cli {wver}", 0)
        if args.development_service in [1, "1"]:
            loggingC.message((">Initializing a test submission to " \
                               "the ENA dev server."), 0)
            if args.minitest:
                loggingC.message(">Minitest: This mode will use only a small "
                                 "fraction of you dataset for submission "
                                 "testing. Please run a test submission "
                                 "with the complete dataset before submitting "
                                 "to the production service.", 0)
        else:
            loggingC.message((">Initializing a LIVE SUBMISSION to " \
                               "the ENA production server."), 0)
            time.sleep(10) # Give user some extra time to notice message
        print(" ")

        if not args.skip_checks:
            utility.validate_parameter_combination(args.submit_samples,
                                                   args.submit_reads,
                                                   args.submit_assembly,
                                                   args.submit_bins,
                                                   args.submit_mags)

        msg = utility.print_submission_schedule(args.submit_samples,
                                                args.submit_reads,
                                                args.submit_assembly,
                                                args.submit_bins,
                                                args.submit_mags)
        loggingC.message(msg, threshold=0)

        config = preflight.preflight_checks(vars(args))

        # If we are submitting bins, get the quality scores and the
        # taxonomic information.
        # We do this early so we notice issues before we start staging files.
        if args.submit_bins or args.submit_mags:
            bin_quality = get_bin_quality(config, silent=True)
            # If there are quality cutoffs, make a list of bins to submit
            filtered_bins = utility.quality_filter_bins(bin_quality, config)
            # Test if there are bins which are too contaminated
            for name in filtered_bins:
                contamination = bin_quality[name]['contamination']
                if contamination > staticConfig.max_contamination:
                    err = (
                        f"\nERROR: Bin {name} has a contamination score "
                        f"of {contamination} which is higher than "
                        f"{staticConfig.max_contamination}"
                    )
                    err += (
                        "\nENA will reject the submission of this "
                        "bin. Consult the 'Contamination above 100%' "
                        "of README.md for more information."
                    )
                    loggingC.message(err, threshold=-1)
                    exit(1)
            # Query the taxonomy of bins
            bin_taxonomy = taxQuery.get_bin_taxonomy(filtered_bins, config)
            if args.minitest:
                msg = f">Minitest: Discarding every bin except {filtered_bins[0]}"
                loggingC.message(msg, threshold=0)
                filtered_bins = filtered_bins[0:1]
            
        # Construct depth files if there are .bam files in the config
        if 'BAM_FILES' in config.keys():
            bam_files = utility.from_config(config, 'BAM_FILES')

            if not isinstance(bam_files, list):
                bam_files = [bam_files]
            if args.minitest:
                msg = f">Minitest: Ignoring bam files except for {bam_files[0]}"
                loggingC.message(msg, threshold=0)
                bam_files = bam_files[0:1]
            depth_files = utility.construct_depth_files(args.staging_dir,
                                                        args.threads,
                                                        bam_files)
            bin_coverage_file = None
        else:
            if args.submit_bins:
                bin_coverage_file = utility.from_config(config,
                                                        'BINS',
                                                        'COVERAGE_FILE')
            depth_files = None

        if args.submit_samples:
            sample_accession_data = submit_samples(config,
                                                   args.staging_dir,
                                                   args.logging_dir,
                                                   test=args.development_service)
        else:
            if args.submit_assembly or args.submit_bins or args.submit_mags:
                sample_accessions = utility.from_config(config,
                                                        'SAMPLE_ACCESSIONS')
            else:
                # We are only submitting reads. We need to collect the sample
                # accessions from the individual read entries in the config.
                sample_accessions = utility.samples_from_reads(config)

            if not isinstance(sample_accessions, list):
                sample_accessions = [sample_accessions]
            sample_accession_data = []
            for acc in sample_accessions:
                sample_accession_data.append({
                    'accession': acc,
                    'external_accession': 'unk',
                    'alias': 'unk',
                })
            
        if args.submit_reads:
            run_accessions = submit_reads(config,
                                          sample_accession_data,
                                          prepdir(args.staging_dir, 'reads'),
                                          prepdir(args.logging_dir, 'reads'),
                                          test=args.development_service,
                                          minitest=args.minitest)
        else:
            if args.submit_bins or args.submit_mags or args.submit_assembly:
                run_accessions = utility.from_config(config, 'ASSEMBLY', 'RUN_ACCESSIONS')
                if not isinstance(run_accessions, list):
                    run_accessions = [run_accessions]

        if args.submit_assembly:
            assembly_sample_accession, assembly_fasta_accession = submit_assembly(config,
                                                                                  args.staging_dir,
                                                                                  args.logging_dir,
                                                                                  depth_files,
                                                                                  sample_accession_data,
                                                                                  run_accessions,
                                                                                  threads=args.threads,
                                                                                  test=args.development_service)
            # Assembly sample accession will be either the accession of the
            # co-assembly virtual sample or the accession of the single sample
            # which the assembly is based on
        else:
            if args.submit_bins or args.submit_mags:
                # In this case we need the submission of the sample that the
                # assembly is based on. We can derive it from the assembly
                # accession by querying ENA
                assembly_dict = utility.from_config(config, 'ASSEMBLY')
                assembly_sample_accession = None
                if 'EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION' in assembly_dict.keys():
                    if not assembly_dict['EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION'] is None:
                        assembly_sample_accession = assembly_dict['EXISTING_CO_ASSEMBLY_SAMPLE_ACCESSION']
                if 'EXISTING_ASSEMBLY_ANALYSIS_ACCESSION' in assembly_dict.keys():
                    if not assembly_dict['EXISTING_ASSEMBLY_ANALYSIS_ACCESSION'] is None:
                        assembly_analysis_accession = assembly_dict['EXISTING_ASSEMBLY_ANALYSIS_ACCESSION']
                        assembly_sample_accession = enaSearching.search_samples_by_assembly_analysis(assembly_analysis_accession,
                                                                                                    args.development_service)

        # Bin submision
        if args.submit_bins:
            submit_bins(filtered_bins,
                        config,
                        bin_taxonomy,
                        sample_accession_data,
                        run_accessions,
                        prepdir(args.staging_dir, 'bins'),
                        prepdir(args.logging_dir, 'bins'),
                        depth_files,
                        bin_coverage_file,
                        threads=args.threads,
                        test=args.development_service)


        # MAG submission
        if args.submit_mags:
            if args.submit_assembly:
                metagenome_scientific_name = utility.from_config(config, 'METAGENOME_SCIENTIFIC_NAME')
            else:
                try:
                    metagenome_scientific_name = enaSearching.search_scientific_name_by_sample(assembly_sample_accession,
                                                                                                args.development_service)
                except:  
                    # This is a workaround for times where the ENA development
                    # API does not work. If the sample is registered on the 
                    # production server we can still continue submitting.
                    # Included because the situation came up multiple times
                    # during development.
                    metagenome_scientific_name = enaSearching.search_scientific_name_by_sample(assembly_sample_accession,
                                                                                                False)
            submit_mags(config,
                        metagenome_scientific_name,
                        sample_accession_data,
                        run_accessions,
                        bin_taxonomy,
                        prepdir(args.staging_dir, 'mags'),
                        prepdir(args.logging_dir, 'mags'),
                        depth_files,
                        bin_coverage_file,
                        threads=args.threads,
                        test=args.development_service)

        msg = "\n>All submissions completed."
        if args.development_service:
            msg += (
                "\n>This was a TEST submission to the ENA development "
                "server."
                "\n>You can check the status of your submission by "
                "logging into the development instance of the ENA "
                "submission website."
                "\n>Since this was a test submission, you will not "
                "receive final accessions via mail."
                "\n>Your data will be removed from the development "
                "server during the next 24 hours."
            )
        else:
            msg += (
                "\n>You will receive final accessions once your "
                "submission has been processed by ENA."
                "\n>ENA will send those final accession by email to "
                "the contact adress of your ENA account."
            )
        loggingC.message(msg, threshold=0)

        # Cleanup
        if not args.keep_depth_files and depth_files is not None:
            loggingC.message(">Deleting depth files to free up disk space.", threshold=0)
            for depth_file in depth_files:
                os.remove(depth_file)

    except Exception:
        err = "\n\nTERMINATING BECAUSE AN UNEXPECTED ERROR OCCURED:\n"
        loggingC.message(err, threshold=-1)
        exc_info = traceback.format_exc()
        loggingC.message(exc_info, threshold=-1)
        exit(1)


