import os

from submg.core import (
    init_argparse,
    download_webin,
    makecfg,
    submit,
)

def main():
    parser = init_argparse()
    args = parser.parse_args()
    if args.mode == 'download-webin':
        download_webin()
    elif args.mode == 'makecfg':
        if os.path.isdir(args.outfile):
            parser.error(f"Output path '{args.outfile}' is a directory; specify a file.")
        if min(args.submit_samples, args.submit_unpaired_reads,
               args.submit_paired_end_reads) < 0:
            parser.error("Sample and read counts must be non-negative.")
        makecfg(args)
    elif args.mode == 'submit':
        if args.threads < 1:
            parser.error("--threads must be at least 1.")
        submit(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
