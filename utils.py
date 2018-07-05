import argparse
import logging
import sys
from distutils.version import LooseVersion


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


def not_newer(version_1, version_2):
    return LooseVersion(version_1) <= LooseVersion(version_2)


def is_older(version_1, version_2):
    return LooseVersion(version_1) < LooseVersion(version_2)
