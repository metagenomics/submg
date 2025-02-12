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
        makecfg(args)
    elif args.mode == 'submit':
        submit(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
