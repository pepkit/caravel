""" General-purpose functions """

from __future__ import print_function
import glob
from itertools import chain
import random
import string
import sys
if sys.version_info < (3, 3):
    from collections import Iterable
else:
    from collections.abc import Iterable
import argparse

__version__ = 0.1

def coll_like(c):
    """
    Determine whether an object is collection-like
    :param object c: object to test
    :return bool: whether the argument is a (non-string) collection
    """
    return isinstance(c, Iterable) and not isinstance(c, str)


def eprint(*args, **kwargs):
    """
    Print the provided text to stderr.
    """
    print(*args, file=sys.stderr, **kwargs)


def geprint(txt):
    """
    Print the provided text to stderr in green. Used to print the token for the user.
    :param txt: string with text to be printed.
    """
    eprint("\033[92m {}\033[00m".format(txt))


def flatten(x):
    """
    Flatten one level of nesting
    :param x: a list to flatten
    :return list[str]: a flat list
    """
    return list(chain.from_iterable(x))


def glob_if_exists(x):
    """
    Return all matches in the directory for x and x if nothing matches
    :param x: a string with path containing globs
    :return list[str]: a list of paths
    """
    return [glob.glob(e) or e for e in x] if coll_like(x) else (glob.glob(x) or [x])


def random_string(n):
    """
    Generates a random string of length N (token), prints a message
    :param int n: length of the string to be generated
    :return str: random string
    """
    eprint("CSRF token generated")
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(n))


def build_parser():
    """
    Building argument parser.
    :return argparse.ArgumentParser
    """

    # Main caravel program help text messages
    banner = "%(prog)s - Run a web interface for looper."

    parser = _VersionInHelpParser(
            description=banner,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            "-V", "--version",
            action="version",
            version="%(prog)s {v}".format(v=__version__))

    parser.add_argument(
            "-c", "--config",
            dest="config",
            help="Config file (YAML). If not provided the environment variable $CARAVEL will be used instead.")

    parser.add_argument(
            "-d", "--debug-mode",
            action="store_true",
            dest="debug",
            help="Use this option if you want to enter the debug mode.")
    return parser


class _VersionInHelpParser(argparse.ArgumentParser):
    def format_help(self):
        """ Add version information to help text. """
        return "version: {}\n".format(__version__) + \
               super(_VersionInHelpParser, self).format_help()
