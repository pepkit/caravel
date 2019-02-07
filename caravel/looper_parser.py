""" Interface with looper """

import argparse
from const import SET_ELSEWHERE

__all__ = ["get_long_optnames", "get_html_elements_info", "opts_by_prog"]


def get_long_optnames(p):
    """
    Map each program/subcommand name to collection of long option names.

    :param argparse.ArgumentParser p: the CLI parser to inspect
    :return dict[str, Iterable[str]]: binding between program/subcommand name
        and collection of option names for it
    """

    def use_act(a):
        return not _is_set_elsewhere(a.option_strings)

    def get_name(a):
        if not _is_set_elsewhere(a.option_strings):
                return _get_long_opt(a.option_strings)

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


def _is_set_elsewhere(opt):
    """
    Check if the option is set elsewhere in caravel. Return True if yes.
    For example the compute env is configured in a separate tab, at the project level.
    Additionally, options like "--help" or "-version" are treated the same way
    :param list opt: list with one element. Option to be checked.
    :return:
    """
    return [_get_long_opt(opt)] in SET_ELSEWHERE


# def get_options_html_types(p, command=None):
#     """
#     Determine the type of the HTML form element from the looper parser/subparser.
#     Addtionally, get a list of dictionaries with the HTML elements parameters and corresponding values
#     needed to construct the objects and the dest values.
#     _HelpAction objects (--help), _VersionAction objects and empty option_strings are omitted
#
#     :param argparse.ArgumentParser p: the parser to inspect
#     :param str command: looper command name if no name provided the main parser is used
#     :return: html_element_type: name of the html elements to use
#     :return: html_params: parameters needed for HTML form elements construction
#     :rtype: (list, list[dict])
#     """
#     if command is None:
#         opts = p._actions
#     else:
#         subparser = _get_subparser(p)
#         opts = subparser.choices[command]._actions
#
#     html_elements_types = []
#     html_params = []
#     html_dest = []
#     for opt in opts:
#         if _is_set_elsewhere(opt.option_strings):
#             continue
#         elif isinstance(opt, argparse._StoreFalseAction) or isinstance(opt, argparse._StoreTrueAction):
#             html_elements_types.append("checkbox")
#             html_params.append({"checked": "True"}) if opt.default else html_params.append({None: None})
#             html_dest.append(opt.dest)
#         elif isinstance(opt, argparse._StoreAction):
#             if opt.choices is not None:
#                 html_elements_types.append("select")
#                 html_dest.append(opt.dest)
#                 if opt.choices is not None:
#                     html_params.append({"value": opt.choices})
#             elif opt.type is not None and isinstance(opt.type(), (int, float)):
#                 html_elements_types.append("range")
#                 html_params.append({"step": "1"}) if isinstance(opt.type(), int) else html_params.append({"step": "0.1"})
#                 html_dest.append(opt.dest)
#             else:
#                 # will use custom type info from looper here
#                 html_elements_types.append("text")
#                 html_params.append({"placeholder": "Unknown argument type"})
#                 html_dest.append(opt.dest)
#         else:
#             html_elements_types.append("text")
#             html_params.append({"placeholder": "Unknown argument type"})
#             html_dest.append(opt.dest)
#     ret_vals_lens = set(map(len, [html_elements_types, html_params, html_dest]))
#     assert len(ret_vals_lens) == 1, "The lengths of return lists are not equal, '{}'".format(ret_vals_lens)
#     return html_elements_types, html_params, html_dest


def get_html_elements_info(p, command=None):
    """
    Determine the type of the HTML form element from the looper parser/subparser.
    Additionally, get a list of dictionaries with the HTML elements parameters and corresponding values
    needed to construct the objects and the dest values.
    See _is_set_elsewhere documentation for the options that are omitted.

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
    opt_names = []
    for opt in opts:
        if _is_set_elsewhere(opt.option_strings):
            continue
        else:
            opt_names.append(_get_long_opt(opt.option_strings))
            type_data = opt.type("1", caravel=True)
            type = type_data.element_type
            params = type_data.element_args
            html_elements_types.append(type)
            html_params.append(params)
            html_dest.append(opt.dest)
    ret_vals_lens = set(map(len, [html_elements_types, html_params, html_dest, opt_names]))
    assert len(ret_vals_lens) == 1, "The lengths of return lists are not equal, '{}'".format(ret_vals_lens)
    return html_elements_types, html_params, html_dest, opt_names


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


def _has_long_opt(opt):
    """
    Determine whether the given option defines a long option name

    :param list opt: a list of option name(s)
    :return: bool indicating whether the given option defines a long option name

    """
    if not isinstance(opt, list):
        raise TypeError("The opt argument has to be a list of strings.")
    for n in opt:
        if _is_long_optname(n):
            return True
    return False


def _get_long_opt(opt):
    """
    Get only the long option name from the option strings

    :param list opt: a list of option name(s)
    :return: a long option name or empty string
    """
    if _has_long_opt(opt):
        return opt[map(_is_long_optname, opt).index(True)]
    else:
        return ""


def _is_long_optname(n):
    """ Determine whether a given option name is "long" form. """
    return n.startswith("--")
