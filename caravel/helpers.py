""" General-purpose functions """

from __future__ import print_function
import argparse
import glob
from itertools import chain
import random
import string
import sys
import looper
import peppy
import fcntl
import termios
import struct
from flask import render_template
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
    :return str: a random string
    """
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(n))


def render_error_msg(msg):
    """
    Renders an error template with a message and prints to the terminal

    :param str msg: the message to be printed and displayed on the web
    """
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
            version=_version_text())

        self.add_argument(
            "-c", "--config",
            dest="config",
            help="Config file (YAML). If not provided the environment variable "
                 "CARAVEL will be used instead.")

        self.add_argument(
            "-p", "--port",
            dest="port",
            help="The port the webserver should be run on.", default=DEFAULT_PORT)

        self.add_argument(
            "-d", "--dbg",
            action="store_true",
            dest="debug",
            help="Use this option if you want to enter the debug mode. Unsecured.")

    def format_help(self):
        """ Add version information to help text. """
        return _version_text() + super(CaravelParser, self).format_help()


def _version_text():
    """
    Compile a string for the argparser help with caravel and looper versions

    :return str: a compiled string
    """
    return "caravel version: {cv}\nlooper version: {lv}\n".format(cv=CARAVEL_VERSION, lv=LOOPER_VERSION)


def print_terminal_width(txt=None, char="-"):
    """
    Print a line composed of the chars and a text in the middle of the terminal

    :param str txt: a string to display in the middle of the terminal
    :param str char: a character that the box will be composed of
    """
    char = str(char)
    assert len(char) == 1, "The length of the char parameter has to be equal 1, got '{}'".format(len(char))
    spaced_txt = txt.center(len(txt)+2) if txt is not None else ""
    fill_width = int(0.5 * (terminal_width() - len(spaced_txt)))
    filler = char * fill_width
    print(filler + spaced_txt + filler)


def terminal_width():
    """
    Get terminal width

    :return int: width of the terminal
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
