#!/usr/bin/env python

import argparse
import os
import time

from synum import utility, preflight, configGen
from synum.statConf import staticConfig

from synum.sampleSubmission import submit_samples
from synum.readSubmission import submit_reads
from synum.assemblySubmission import submit_assembly
from synum.binSubmission import submit_bins, get_bin_taxonomy, get_bin_quality


def main():
    """
    Main function.
    """
    
    # Parsing command line input
    parser = argparse.ArgumentParser(description="""Tool for submitting metagenome bins to the European Nucleotide Archive.
                                     Environment variables ENA_USER and ENA_PASSWORD must be set for ENA upload.""")
    parser.add_argument("-v", "--version",          action="version", version=f"%(prog)s {staticConfig.synum_version}")
    

    subparsers = parser.add_subparsers(dest='mode')

    
    parser_submit = subparsers.add_parser('submit', help='Stage your data and submit it to either the ENA development or production server')
    parser_submit.add_argument("-x", "--config",           required=True,          help="Path to the YAML file containing metadata and filepaths. Mandatory")
    parser_submit.add_argument("-s", "--staging_dir",      required=True,          help="Directory where files will be staged for upload. Must be empty. May use up a lot of disk space. Mandatory.")
    parser_submit.add_argument("-l", "--logging_dir",      required=True,          help="Directory where log files will be stored. Must be empty. Mandatory.")
    parser_submit.add_argument("-y", "--verbosity",        type=int, choices=[0, 1, 2], default=1, help="Control the amount of logging to stdout. [default 1]")
    parser_submit.add_argument("-d", "--devtest",          type=int, choices=[0, 1], default=1, help="Make submissions to the ENA dev test server. [default 1/true]")
    parser_submit.add_argument("-t", "--threads",          type=int, default=4, help="Number of threads used to process .bam files. [default 4]")
    parser_submit.add_argument("--keep_depth_files", action="store_true",    help="Do not delete depth files after running. [default false]")
    parser_submit.add_argument("-r", "--submit_reads",    action="store_true", default=False,    help="Use if you want to submit reads.")
    parser_submit.add_argument("-p", "--submit_samples",  action="store_true", default=False,    help="Use if you want to submit (biological) sample objects.")
    parser_submit.add_argument("-a", "--submit_assembly",action="store_true", default=False,     help="Use if you want to submit one assembly. To submit multiple assemblies, you need to use the tool multiple times.")
    parser_submit.add_argument("-b", "--submit_bins",    action="store_true", default=False,    help="Use if you want to submit metagenome bins (note that bins are different from MAGs in the ENA definition).")
    parser_submit.add_argument("-m", "--submit_mags",    action="store_true", default=False,    help="Use if you want to submit metagenome-assembled genomes (MAGs).")

    parser_makecfg = subparsers.add_parser('makecfg', help='Create a .yml file containing the fields you need to fill out prior to submission')
    parser_makecfg.add_argument("-o", "--outfile",           required=True,          help="Path to the empty config that will be generated.")
    parser_makecfg.add_argument("-s", "--submit_samples", type=int, default=0,     help="If you want to submit (biological) sample objects, specify how many.")    
    parser_makecfg.add_argument("-rs", "--submit_single_reads",   type=int, default=0,     help="If you want to submit non-paired read files, specify how many.")
    parser_makecfg.add_argument("-rp", "--submit_paired_end_reads",   type=int, default=0,     help="If you want to submit paired-end read files, specify how many.")
    parser_makecfg.add_argument("-b", "--submit_bins",    action="store_true", default=False,    help="Use if you want to submit metagenome bins (note that bins are different from MAGs in the ENA definition).")
    parser_makecfg.add_argument("-m", "--submit_mags",    action="store_true", default=False,    help="Use if you want to submit metagenome-assembled genomes (MAGs).")
    parser_makecfg.add_argument("-a", "--submit_assembly",action="store_true", default=False,     help="Use if you want to submit one assembly. To submit multiple assemblies, you need to use the tool multiple times.")

    coverage_group = parser_makecfg.add_mutually_exclusive_group(required=True)
    coverage_group.add_argument("--coverage_from_bam", action="store_true", help="Coverages will be calculated from a list of .bam files that you provide.")
    coverage_group.add_argument("--known_coverage", action="store_true", help="Coverages are already known and you provide them as a .bam file.")


    args = parser.parse_args()

    if args.mode == 'makecfg':
        configGen.make_config(outpath=args.outfile,
                              submit_samples=args.submit_samples,
                              submit_single_reads=args.submit_single_reads,
                              submit_paired_end_reads=args.submit_paired_end_reads,
                              coverage_from_bam=args.coverage_from_bam,
                              known_coverage=args.known_coverage,
                              submit_assembly=args.submit_assembly,
                              submit_bins=args.submit_bins,
                              submit_mags=args.submit_mags)


    elif args.mode == 'submit':

        verbose = args.verbosity

        # Print version
        if verbose>0:
            print(f">Running synum version {staticConfig.synum_version}")
            if args.devtest == 1:
                print(">Initializing a test submission to the ENA dev server.")
            else:
                print(">Initializing a LIVE SUBMISSION to the ENA production server.")
                time.sleep(3)

        config = preflight.preflight_checks(args, verbose)

        # If we are submitting bins, get the quality scores and the
        # taxonomic information.
        # We do this early so we notice issues before we start staging files.
        if args.submit_bins or args.submit_mags:
            bin_quality = get_bin_quality(config, verbose=0)
            # Test if there are bins which are too contaminated
            for name in bin_quality.keys():
                contamination = bin_quality[name]['contamination']
                if contamination > staticConfig.max_contamination:
                    print(f"\nERROR: Bin {name} has a contamination score of {contamination} which is higher than {staticConfig.max_contamination}")
                    print(f"ENA will reject the submission of this bin. Consult the 'Contamination above 100%' of README.md for more information.")
                    exit(1)
            bin_taxonomy = get_bin_taxonomy(config, verbose)
        
        # Construct depth files if there are .bam files in the config
        if 'BAM_FILES' in config.keys():
            bam_files = utility.from_config(config, 'BAM_FILES')
            if not isinstance(bam_files, list):
                bam_files = [bam_files]
            depth_files = utility.construct_depth_files(args.staging_dir,
                                                        args.threads,
                                                        bam_files,
                                                        verbose)
            bin_coverage_files = None
        else:
            if args.submit_bins:
                bin_coverage_files = utility.from_config(config, 'BINS', 'COVERAGE_FILES')
                if not isinstance(bin_coverage_files, list):
                    bin_coverage_files = [bin_coverage_files]
            depth_files = None

        if args.submit_samples:
            sample_accession_data = submit_samples(config,
                                               args.staging_dir,
                                               args.logging_dir,
                                               verbose=verbose,
                                               test=args.devtest)
        else:
            sample_accessions = utility.from_config(config, 'SAMPLE_ACCESSIONS')
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
                                          args.staging_dir,
                                          args.logging_dir,
                                          verbose=verbose,
                                          test=args.devtest)
        else:
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
                                                                                  verbose=verbose,
                                                                                  test=args.devtest)
            

        # Bin submision
        if args.submit_bins:
            submit_bins(config,
                        bin_taxonomy,
                        assembly_sample_accession,
                        args.staging_dir,
                        args.logging_dir,
                        depth_files,
                        threads=args.threads,
                        verbose=verbose,
                        test=args.devtest)

        print(">You will receive final accessions once your submission has been processed by ENA.")
        print(">ENA will send those final accession by email to the contact adress of your ENA account.")


        # EVERYTHING BELOW HAS TO BE REWORKED
        exit(1)


        # MAG submission
        # TODO

        # Cleanup
        if not args.keep_depth_files:
            if verbose>0:
                print(">Deleting depth files to free up disk space.")
            for depth_file in depth_files:
                os.remove(depth_file)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()

