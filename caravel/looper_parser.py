""" Interface with looper """

import argparse
from distutils.version import LooseVersion
from const import SET_ELSEWHERE, REQUIRED_LOOPER_VERSION, LOOPER_VERSION

__all__ = ["get_long_optnames", "get_html_elements_info", "opts_by_prog", "html_param_builder", "convert_value",
           "parse_namespace", "ensure_looper_version"]


def ensure_looper_version(required_looper=REQUIRED_LOOPER_VERSION, current_looper=LOOPER_VERSION):
    """
    Loose looper version assertion.

    The distutils.version.LooseVersion objects implement __cmp__ methods that allow for
     comparisons of version strings with letters, like: "0.11.0dev".

    :param str required_looper: A version that is required for the software to function
    :param str current_looper: A version that the software uses
    :return:
    """
    assert LooseVersion(current_looper) >= LooseVersion(required_looper), \
        "The version of looper in use ({in_use}) does not meet the caravel requirement ({req})"\
            .format(in_use=current_looper, req=required_looper)


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
            html_params.append(html_param_builder(params))
            html_dest.append(opt.dest)
    ret_vals_lens = set(map(len, [html_elements_types, html_params, html_dest, opt_names]))
    assert len(ret_vals_lens) == 1, "The lengths of return lists are not equal, '{}'".format(ret_vals_lens)
    return [html_elements_types, html_params, html_dest, opt_names]


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


def html_param_builder(params):
    """
    Build a HTML params string out of a dictionary of the option names and their values. If a list is the value
    (it is intended in a select case) the original list is returned instead of a string

    :param dict params:
    :return: the composed parameters string or list in case list is the class of the value in the dict
    :rtype: str | list
    """
    string = ""
    for key, value in params.items():
        if isinstance(value, list):
            return value
        string = string + key + "=" + value + " "
    return string.strip()


def parse_namespace(var_nspce):
    """
    Process the dictionary (e.g. produced by vars(argparse.Namespace)). Change None to False (produced by checkboxes)
    and "on" to True

    :param dict var_nspce:
    :return: processed dict. Keep in ming that if the input was the output of vars(argparse.Namespace) the argparse.Namespace will update as well./
    :rtype dict
    """
    for key, value in var_nspce.items():
        if value is None and key is not "subproject":
            var_nspce[key] = False
        elif value == "on":
            var_nspce[key] = True
    return var_nspce


def convert_value(val):
    """
    Convert string to the most appropriate type, one of: bool, str, int, None or float

    :param str val: the string to convert
    :return: converted string to the most appropriate type
    :rtype bool | str | int | float | None
    """
    if not isinstance(val, str):
        try:
            val = str(val)
        except:
            raise ValueError("The input has to be of type convertible to 'str', got '{}'".format(type(val)))

    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        if val == 'None':
            return None
        try:
            float(val)
        except ValueError:
            return val
        else:
            try:
                int(val)
            except ValueError:
                return float(val)
            else:
                return int(val)
