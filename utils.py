import argparse
import logging


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("jenkins_plugins_config")
    parser.add_argument("download_dir")
    parser.add_argument("-d", "--debug", help="Turn on debug messages",
                        action="store_true")
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    return args
