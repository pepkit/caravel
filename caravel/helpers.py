""" General-purpose functions """

import glob
from itertools import chain
import sys
if sys.version_info < (3, 3):
    from collections import Iterable
else:
    from collections.abc import Iterable
import argparse


def coll_like(c):
    """
    Determine whether an object is collection-like
    :param object c: object to test
    :return bool: whether the argument is a (non-string) collection
    """
    return isinstance(c, Iterable) and not isinstance(c, str)


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


def get_subparser(parser):
    """
    Get the argparse._SubParsersAction objects from argparse.ArgumentParser object
    :param parser: argparse.ArgumentParser object with subparser
    :return: list of subparsers (argparse._SubParsersAction objects) in the parser (argparse.ArgumentParser object)
    """
    idx = [isinstance(x, argparse._SubParsersAction) for x in parser._actions].index(True)
    return parser._actions[idx]




def get_commands(parser):
    """
    Get the commands from subparser in parser
    :param parser: argparse.ArgumentParser object with subparser
    :return: list[str]: a list of commands available in subparser
    """
    subparser = get_subparser(parser)
    subcommands_subparsers = subparser.choices
    commands = subcommands_subparsers.keys()
    return commands
