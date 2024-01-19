import os

from synum.statConf import staticConfig

# Global variables for logging
logfile_path = None
verbosity_level = None

def set_up_logging(logging_dir: str,
                   verbose: int):
    """
    Set up logging.

    Args:
        logfile: The path to the logfile.
        verbose: The verbosity level.
    """
    # Set up global variables
    global logfile_path
    global verbosity_level
    logfile_path = os.path.join(logging_dir, 'synum.log')
    verbosity_level = verbose

    # Create logging dir if it doesn't exist
    if not os.path.exists(logging_dir):
        os.makedirs(logging_dir)

    # Check if logging dir is empty
    if os.listdir(logging_dir):
        print(f"\nERROR: Logging directory is not empty: {logging_dir}")
        exit(1)

    # Create empty logfile
    with open(logfile_path, 'w') as f:
        f.write('')


def message(message: str,
            threshold: int = -1):
    """
    Log a message to the logfile and print it to stdout if the verbosity level is high enough.

    Args:
        message:   The message to log.
        threshold: The verbosity level threshold.
    """
    global logfile_path
    global verbosity_level

    # Make sure the log file exists
    if not os.path.isfile(logfile_path):
        print(f"\nERROR: There should be a logfile at {logfile_path} but it seems to have been deleted.")
        exit(1)

    # Write a new line to the logfile
    with open(logfile_path, 'a') as f:
        f.write(f"{message}\n")

    # Print to stdout if the verbosity level is high enough
    if verbosity_level > threshold:
        print(message)