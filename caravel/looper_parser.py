""" Interface with looper """

import argparse

# __all__ = ["get_long_optnames", "opts_by_prog"]


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


def get_options_html_types(p, command=None):
    """
    Determine the type of the HTML form element from the looper parser/subparser.
    Addtionally, get a list of dictionaries with the HTML elements parameters and corresponding values
    needed to construct the objects and the dest values.
    _HelpAction objects (--help), _VersionAction objects and empty option_strings are omitted

    :param argparse.ArgumentParser p: the parser to inspect
    :param str command: looper command name if no name provided the main parser is used
    :return: html_element_type: name of the html elements to use
    :return: html_params: parameters needed for HTML form elements construction
    :rtype: (list, list[dict])
    """
    if command is None:
        opts = p._actions
    else:
        subparser = _get_subparser(p)
        opts = subparser.choices[command]._actions

    html_elements_types = []
    html_params = []
    html_dest = []
    for opt in opts:
        if isinstance(opt, (argparse._HelpAction, argparse._VersionAction)) or not opt.option_strings or opt.option_strings == ["--sp"]:
            continue
        elif isinstance(opt, argparse._StoreFalseAction) or isinstance(opt, argparse._StoreTrueAction):
            html_elements_types.append("checkbox")
            html_params.append({"checked": "True"}) if opt.default else html_params.append({None: None})
            html_dest.append(opt.dest)
        elif isinstance(opt, argparse._StoreAction):
            if opt.choices is not None:
                html_elements_types.append("select")
                html_dest.append(opt.dest)
                if opt.choices is not None:
                    html_params.append({"value": opt.choices})
            elif opt.type is not None and isinstance(opt.type(), (int, float)):
                html_elements_types.append("range")
                html_params.append({"step": "1"}) if isinstance(opt.type(), int) else html_params.append({"step": "0.1"})
                html_dest.append(opt.dest)
            else:
                # will use custom type info from looper here
                html_elements_types.append("text")
                html_params.append({"placeholder": "Unknown argument type"})
                html_dest.append(opt.dest)
        else:
            html_elements_types.append("text")
            html_params.append({"placeholder": "Unknown argument type"})
            html_dest.append(opt.dest)
    return html_elements_types, html_params, html_dest


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
