""" General-purpose functions """

from __future__ import print_function
import argparse
import glob
from itertools import chain
import os
import random
import string
import sys
import looper
import peppy
import fcntl
import termios
import struct
from const import *


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
    return [glob.glob(e) or e for e in x] if peppy.utils.coll_like(x) else (glob.glob(x) or [x])


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
           "looper version: {}\n".format(looper_version)


def print_terminal_width(txt=None, char="-"):
    """
    Print a line composed of the chars and a text in the middle of the terminal

    :param str txt: a string to display in the middle of the terminal
    :param str char: a character that the box will be composed of
    :return None
    """
    char = str(char)
    assert len(char) == 1, "The length of the char parameter has to be equal 1, got '{}'".format(len(char))
    spaced_txt = txt.center(len(txt)+2) if txt is not None else ""
    print(char * int((terminal_width() / 2) - (len(spaced_txt) / 2)) + spaced_txt + char *
          int((terminal_width() / 2) - (len(spaced_txt) / 2)))


def terminal_width():
    """
    Get terminal width

    :return: width of the terminal
    :rtype int
    """
    _, tw = struct.unpack('HH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HH', 0, 0)))
    return tw


def run_looper(prj, args, act, log_path, logging_lvl):
    """
    Prepare and run looper action using the provided arguments

    :param looper.project.Project prj: project to execute looper action on
    :param argparse.Namespace args: set of looper arguments
    :param str act: action to run
    :param str log_path: absolute path to the log file location
    :param int logging_lvl: logging level code
    :return: None
    """
    # Establish looper logger
    looper.setup_looper_logger(level=logging_lvl, additional_locations=log_path)
    # run selected looper action
    with peppy.ProjectContext(prj) as prj:
        if act == "run":
            run = looper.looper.Runner(prj)
            try:
                print_terminal_width("looper log")
                run(args, None)
                print_terminal_width()
            except IOError:
                raise Exception("{} pipelines_dir: '{}'".format(
                    prj.__class__.__name__, prj.metadata.pipelines_dir))

        if act == "destroy":
            print_terminal_width("looper log")
            looper.looper.Destroyer(prj)(args)
            print_terminal_width()

        if act == "summarize":
            print_terminal_width("looper log")
            looper.looper.Summarizer(prj)()
            print_terminal_width()

        if act == "check":
            print_terminal_width("looper log")
            looper.looper.Checker(prj)(flags=args.flags)
            print_terminal_width()

        if act == "clean":
            print_terminal_width("looper log")
            looper.looper.Cleaner(prj)(args)
            print_terminal_width()
