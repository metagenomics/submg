# I don't remember exactly why I wrote this but during development there was
# some issue with the python logging module and this was a quick solution...

import os

# Global variables for logging
logfile_path = None
verbosity_level = None
listeners = []

def set_up_logging(logging_dir: str,
                   verbose: int,
                   listener=None):
    """
    Set up logging.

    Args:
        logfile: The path to the logfile.
        verbose: The verbosity level.
    """
    # Set up global variables
    global logfile_path
    global verbosity_level
    logfile_path = os.path.join(logging_dir, 'submg.log')
    verbosity_level = verbose

    # Handle listeners
    if listener:
        __add_listener(listener)

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


def __add_listener(listener):
    """
    Add a listener function to receive log updates.

    Args:
        listener: A function that takes a log message as an argument.
    """
    global listeners

    listeners.append(listener)


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

    # If verbosity level is high enough
    if verbosity_level > threshold:
        # print to stdout
        print(message)
        # broadcast to listeners
        for listener in listeners:
            listener(message)
