""" General-purpose functions """

from __future__ import print_function
import argparse
import glob
from itertools import chain
import os
import random
import string
import sys
from peppy.utils import coll_like


def eprint(*args, **kwargs):
    """
    Print the provided text to stderr.
    """
    print(*args, file=sys.stderr, **kwargs)


def expand_path(p, root=""):
    """
    Attempt to make a path absolute, by expanding user/env vars.

    :param str p: path to expand
    :param str root: root on which to base relative paths
    :return str: expanded path
    """
    if root:
        if not os.path.isabs(root):
            raise ValueError("Non-absolute root path: {}".format(root))
        def absolutize(x):
            return os.path.join(root, x)
    else:
        def absolutize(x):
            return x
    exp = os.path.expanduser(os.path.expandvars(p))
    return exp if os.path.isabs(exp) else absolutize(exp)


def flatten(x):
    """
    Flatten one level of nesting

    :param x: a list to flatten
    :return list[str]: a flat list
    """
    return list(chain.from_iterable(x))


def geprint(txt):
    """
    Print the provided text to stderr in green. Used to print the token for the user.

    :param txt: string with text to be printed.
    """
    eprint("\033[92m {}\033[00m".format(txt))


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
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(n))


def render_error_msg(msg):
    """ Renders an error template with a message and prints to the terminal. """
    from flask import render_template
    eprint(msg)
    return render_template('error.html', e=[msg], types=None)


class CaravelParser(argparse.ArgumentParser):
    """ CLI parser tailored for this project """

    def __init__(self):

        super(CaravelParser, self).__init__(
            description="%(prog)s - Run a web interface for looper.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        self.add_argument(
            "-V", "--version",
            action="version",
            version=_version_text(sep="; "))

        self.add_argument(
            "-c", "--config",
            dest="config",
            help="Config file (YAML). If not provided the environment variable "
                 "CARAVEL will be used instead.")

        self.add_argument(
            "-d", "--debug-mode",
            action="store_true",
            dest="debug",
            help="Use this option if you want to enter the debug mode. Unsecured.")

    def format_help(self):
        """ Add version information to help text. """
        return _version_text(sep="\n") + super(CaravelParser, self).format_help()


def _version_text(sep):
    from _version import __version__ as caravel_version
    from looper import __version__ as looper_version
    return "caravel version: {}".format(caravel_version) + sep + \
           "looper version: {}".format(looper_version)
