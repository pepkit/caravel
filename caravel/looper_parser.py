""" Interface with looper """

import argparse

__all__ = ["get_long_optnames", "opts_by_prog"]


def get_long_optnames(p):
    """
    Map each program/subcommand name to collection of long option names.

    :param argparse.ArgumentParser p: the CLI parser to inspect
    :return dict[str, Iterable[str]]: binding between program/subcommand name
        and collection of option names for it
    """

    def use_act(a):
        return _has_long_opt(a) and not isinstance(a, argparse._HelpAction)

    def get_name(a):
        for n in a.option_strings:
            if _is_long_optname(n):
                return n
        raise ValueError("No long option names for action: {}".format(a))

    return opts_by_prog(p, get_name=get_name, use_act=use_act)


def opts_by_prog(p, get_name, use_act):
    """
    Bind each program/subcommand name to a collection of option names for it.

    :param argparse.ArgumentParser p: the parser to inspect
    :param callable(argparse.Action) -> str get_name:
    :param callable(argparse.Action) -> bool use_act: how to determine whether
        an action should be "represented" (i.e., if it should have a name
        included in a program's collection)
    :return dict[str, Iterable[str]]: binding between program/subcommand name
        and collection of option names for it
    """
    return {n: [get_name(a) for a in sub._actions if use_act(a)]
            for n, sub in _get_subparser(p).choices.items()}


def _get_subparser(p):
    """
    Return the subparser associated with a CLI opt/arg parser.

    :param argparse.ArgumentParser p: full argument parser
    :return argparse._SubparsersAction: action defining the subparsers
    """
    subs = [a for a in p._actions if isinstance(a, argparse._SubParsersAction)]
    if len(subs) != 1:
        raise ValueError(
            "Expected exactly 1 subparser, got {}".format(len(subs)))
    return subs[0]


def _has_long_opt(act):
    """ Determine whether the given option defines a long option name. """
    try:
        opts = act.option_strings
    except AttributeError:
        opts = []
    for n in opts:
        if _is_long_optname(n):
            return True
    return False


def _is_long_optname(n):
    """ Determine whether a given option name is "long" form. """
    return n.startswith("--")
