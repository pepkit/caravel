""" Interface with looper """

import argparse
from const import SET_ELSEWHERE
from helpers import *


def get_positional_args(p, sort=False):
    """
    Get the looper positional arguments (actions). Additionally, the arguments can be ordered in a practical way

    :param argparse.ArgumentParser p: the parser to inspect
    :param bool sort: if the positional arguemnts should be ordered in a practical way
    :return list: a list of looper positional arguments
    """
    def _sort_looper_actions(act_list):
        order = ["run", "summarize"]
        order.reverse()
        for a in order:
            act_list.remove(a)
            act_list.insert(0, a)
        return act_list

    pos_args = list(_get_subparser(p).choices.viewkeys())
    return _sort_looper_actions(pos_args) if sort else pos_args


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
    Additionally, options like "--help" or "--version" are treated the same way
    :param list opt: list with one element. Option to be checked.
    :return bool: a boolean indicating if an option is set elsewhere
    """
    return [_get_long_opt(opt)] in SET_ELSEWHERE


def get_form_elements_data(parser, project, command=None):
    """
    Determine the type of the HTML form element from the looper parser/subparser.
    Additionally, get a list of dictionaries with the HTML elements parameters and corresponding values
    needed to construct the objects and the dest values.
    See _is_set_elsewhere documentation for the options that are omitted.

    :param argparse.ArgumentParser parser: the parser to inspect
    :param peppy.Project project: the Project in the context of which the data should be processed
    :param str command: looper command name if no name provided the main parser is used
    :return: html_element_type: name of the html elements to use
    :return: html_params: parameters needed for HTML form elements construction
    :rtype: (list, list[dict])
    """
    if command is None:
        opts = parser._actions
    else:
        subparser = _get_subparser(parser)
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
            try:
                type_data = opt.type(caravel=True)
            except TypeError:
                raise TypeError("The option type is not defined for '{}'".format(str(opt.option_strings)))
            type = type_data.element_type
            params = process_type_args(type_data.element_args, project)
            html_elements_types.append(type)
            html_params.append(_html_param_builder(params))
            html_dest.append(opt.dest)
    ret_vals_lens = set(map(len, [html_elements_types, html_params, html_dest, opt_names]))
    assert len(ret_vals_lens) == 1, "The lengths of return lists are not equal, '{}'".format(ret_vals_lens)
    return [html_elements_types, html_params, html_dest, opt_names]


def process_type_args(type_args, project):
    """
    Process the HTML form arguments from the custom type object

    The processing is strictly dependant on the class of the particular parameter. For instance,
    if the argument is a str the processed one will be the value of the Project's attribute named this way.

    :param attmap.AttMap type_args: the HTML form arguments from the type object
    :param peppy.Project project: the Project in the context of which the data should be processed
    :return dict: the dict with processed values
    """
    for k, v in type_args.iteritems():
        if isinstance(v, str):
            type_args[k] = getattr(project, v)
    return type_args


def form_elements_data_by_type(data):
    """
    Group the form elements data into a dictionary by the element type.

    :param list[list] data: output of the get_form_elements_data function, nested list
    :return dict: the data grouped in a way digestible by the HTML templates
    """
    types = data[0]
    opts = data[1]
    dests = data[2]
    optstrings = data[3]
    unique_types = list(set(types))
    ret_dict = dict()
    for i in unique_types:
        indices = find_in_list(i, types)
        sel_opts = get_items(indices, opts)
        sel_dests = get_items(indices, dests)
        sel_optstrings = get_items(indices, optstrings)
        ret_dict.update({i: [sel_opts, sel_dests, sel_optstrings]})
    return ret_dict


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
    :return bool: bool indicating whether the given option defines a long option name

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
    :return str: a long option name or empty string
    """
    if _has_long_opt(opt):
        return opt[list(map(_is_long_optname, opt)).index(True)]
    else:
        return ""


def _is_long_optname(n):
    """ Determine whether a given option name is "long" form. """
    return n.startswith("--")


def _html_param_builder(params):
    """
    Build a HTML params string out of a dictionary of the option names and their values. If a list is the value
    (it is intended in a select case) the original list is returned instead of a string

    :param dict params:
    :return str | list: the composed parameters string or list in case list is the class of the value in the dict
    """
    string = ""
    for key, value in params.items():
        if isinstance(value, list):
            return value
        string = string + key + "=" + str(value) + " "
    return string.strip()


def parse_namespace(var_nspce):
    """
    Process the dictionary (e.g. produced by vars(argparse.Namespace)). Change None to False (produced by checkboxes)
    and "on" to True

    :param dict var_nspce: the dictionary representation of argparse.Namespace to be parsed
    :return dict: processed dict. Keep in mind that if the input was the output of vars(argparse.Namespace)
     the argparse.Namespace will update as well.
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
    :return bool | str | int | float | None: converted string to the most appropriate type
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
