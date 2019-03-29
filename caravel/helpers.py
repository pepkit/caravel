""" General-purpose functions """

from __future__ import print_function
from platform import python_version
import argparse
from const import V_BY_NAME, REQUIRED_V_BY_NAME, DEFAULT_PORT, DEFAULT_TERMINAL_WIDTH, TEMPLATES_PATH, CARAVEL_VERSION, LOOPER_VERSION
import glob
from distutils.version import LooseVersion
from itertools import chain
import random
import string
import sys
import looper
import peppy
import fcntl
import termios
import struct
from flask import render_template, current_app
import os
from re import sub
from functools import partial
from looper.html_reports import *
from looper.looper import Summarizer


def get_items(i, l):
    """
    Get a sublist of list elements by their indices

    :param list[int] i: a list of elements indices
    :param list l: list
    :return list: a list of the desired elements
    """
    return map(l.__getitem__, i)


def compile_results_content(log_path, act):
    """
    Compile the content of the looper results page. Apart from reading the contents of the log file
    (that stores the looper log) a header and a footer are pre/appended.

    :param str log_path: a path to the caravel log file to be shown
    :param str act: the name of the action to be shown in the header of the page
    :return str: the page
    """
    try:
        with open(log_path, "r") as log:
            log_content = log.read()
            compiled_text = "<h2><code>looper {act} </code>results:</br></h2><hr>".format(act=act) +\
                            log_content +\
                            "<hr>log read from <code>{log_path}</code></br>".format(log_path=log_path)
    except IOError:
        compiled_text = "<b>Cannot find the log file: '{}'</b>".format(log_path)
    return _color_to_bold(compiled_text)


def _color_to_bold(txt):
    """
    Replace the color markers (from colorama.Fore) with the HTML bold tags

    :param txt: the string to be edited
    :return str: the uncolored and bolded string
    """
    return sub(pattern=r"\[\d{1}\w{1}", repl="</b>", string=sub(pattern=r"\[\d{2}\w{1}", repl="<b>", string=txt))


def find_in_list(x, l):
    """
    Get indices of the element x in list l

    :param x: element to find
    :param list l: list to be inspected
    :return list: indices of the element
    """
    assert isinstance(l, list), "The argument l has to be a list, got '{}'.".format(type(l))
    return [index for index, value in enumerate(l) if value == x]


def get_summary_html_name(prj):
    """
    Get the name of the summary HTML file for provided project object

    :param peppy.Project prj: a project object to compose a summary HTML file name for
    :return str: name of the summary HTML file
    """
    fname = prj.name
    if prj.subproject is not None:
        fname += "_" + prj.subproject
    return fname + "_summary.html"


def check_for_summary(prj):
    """
    Check if the summary page has been produced

    :param looper.Project prj: project to check for summary for
    :return bool: whether the summary page was produced
    """
    return os.path.exists(os.path.join(prj.metadata.output_dir, get_summary_html_name(prj)))


def ensure_version(current=V_BY_NAME, required=REQUIRED_V_BY_NAME):
    """
    Loose version assertion.

    The distutils.version.LooseVersion objects implement __cmp__ methods that allow for
     comparisons of version strings with letters, like: "0.11.0dev".

    :raise ImportError: if at least one of the versions in use does not meet the requirements
    :return bool: True if all the requested versions match
    """
    assert all(x in current.keys() for x in required.keys()), \
        "the package names to be checked do not match the required versions dictionary."
    for package in required:
        if LooseVersion(current[package]) < LooseVersion(required[package]):
            raise ImportError("The version of {name} in use ({in_use}) does not meet the caravel requirement ({req})"
                            .format(name=package, in_use=current[package], req=required[package]))
    return True


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
            description="%(prog)s - run a web interface for looper",
            epilog="See docs at: http://code.databio.org/caravel/",
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
    return "caravel version: {cv}\nlooper version: {lv}\n".format(cv=V_BY_NAME["caravel"], lv=V_BY_NAME["looper"])


def _print_terminal_width(txt=None, char="-"):
    """
    Print a line composed of the chars and a text in the middle of the terminal

    :param str txt: a string to display in the middle of the terminal
    :param str char: a character that the box will be composed of
    """
    char = str(char)
    assert len(char) == 1, "The length of the char parameter has to be equal 1, got '{}'".format(len(char))
    spaced_txt = txt.center(len(txt)+2) if txt is not None else ""
    fill_width = int(0.5 * (_terminal_width() - len(spaced_txt)))
    filler = char * fill_width
    print(filler + spaced_txt + filler)


def _terminal_width():
    """
    Get terminal width

    :return int: width of the terminal
    """
    try:
        _, tw = struct.unpack('HH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HH', 0, 0)))
    except IOError:
        tw = DEFAULT_TERMINAL_WIDTH
    return tw


def _wrap_func_in_box(func, title):
    """
    This decorator wraps the function output in a titled box

    :param callable func: function to be decorated
    :param str title: the title to be displayed in the center of the box
    :return callable: decorated function
    """
    def decorated(*args, **kwargs):
        _print_terminal_width(title)
        func(*args, **kwargs)
        _print_terminal_width()
    return decorated


wrap_func_in_box = partial(_wrap_func_in_box, title="looper log")


@wrap_func_in_box
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
    eprint("\nAction: {}\n".format(act))
    # run selected looper action
    with peppy.ProjectContext(prj) as prj:
        if act == "run":
            run = looper.looper.Runner(prj)
            try:
                run(args, None)
            except IOError:
                raise Exception("{} pipelines_dir: '{}'".format(prj.__class__.__name__, prj.metadata.pipelines_dir))

        if act == "destroy":
            looper.looper.Destroyer(prj)(args)

        if act == "summarize":
            Summarizer(prj)()
            _render_summary_pages(prj)
        if act == "check":
            looper.looper.Checker(prj)(flags=args.flags)

        if act == "clean":
            looper.looper.Cleaner(prj)(args)


def _render_summary_pages(prj):
    """
    Render the summary pages with caravel navbars and footers

    :param looper.Project prj: a project the summary pages should be create for
    :return:
    """
    # instantiate the objects needed fot he creation the pages
    summarizer = Summarizer(prj)
    html_report_builder = HTMLReportBuilder(prj)
    j_env = get_jinja_env(TEMPLATES_PATH)
    objs = summarizer.objs
    stats = summarizer.stats
    columns = summarizer.columns
    # create navbar links
    links_summary = render_navbar_summary_links(prj, ["summary"])
    links_reports = render_navbar_summary_links(prj, ["reports", "summary"])
    # create navbars
    navbar_summary = render_jinja_template("navbar.html", j_env, dict(summary_links=links_summary))
    navbar_reports = render_jinja_template("navbar.html", j_env, dict(summary_links=links_reports))
    # create footer
    footer_vars = dict(caravel_version=CARAVEL_VERSION, looper_version=LOOPER_VERSION, python_version=python_version(),
                       login=current_app.config["login"])
    footer = render_jinja_template("footer.html", j_env, footer_vars)
    html_report_builder.create_index_html(objs, stats, columns, navbar=navbar_summary, footer=footer)
    save_html(os.path.join(get_reports_dir(prj), "status.html"), html_report_builder.create_status_html(objs, stats, get_reports_dir(prj), navbar_reports, footer))
    save_html(os.path.join(get_reports_dir(prj), "objects.html"), html_report_builder.create_object_parent_html(objs, navbar_reports, footer))
    save_html(os.path.join(get_reports_dir(prj), "samples.html"), html_report_builder.create_sample_parent_html(navbar_reports, footer))
    # Create objects pages
    if not objs.dropna().empty:
        for key in objs['key'].drop_duplicates().sort_values():
            single_object = objs[objs['key'] == key]
            html_report_builder.create_object_html(single_object, navbar_reports, footer)


    if not objs.dropna().empty:
        objs.drop_duplicates(keep='last', inplace=True)

    # Add stats_summary.tsv button link
    tsv_outfile_path = os.path.join(prj.metadata.output_dir, prj.name)
    if hasattr(prj, "subproject") and prj.subproject:
        tsv_outfile_path += '_' + prj.subproject
    tsv_outfile_path += '_stats_summary.tsv'
    stats_file_path = os.path.relpath(tsv_outfile_path, prj.metadata.output_dir)
    # Add stats summary table to index page and produce individual
    # sample pages
    if os.path.isfile(tsv_outfile_path):
        # Produce table rows
        sample_pos = 0
        col_pos = 0
        num_columns = len(columns)
        table_row_data = []
        for row in stats:
            # Match row value to column
            # Row is disordered and does not handle empty cells
            table_row = []
            while col_pos < num_columns:
                value = row.get(columns[col_pos])
                if value is None:
                    value = ''
                table_row.append(value)
                col_pos += 1
            # Reset column position counter
            col_pos = 0
            sample_name = str(stats[sample_pos]['sample_name'])
            # Order table_row by col_names
            sample_stats = OrderedDict(zip(columns, table_row))
            table_cell_data = []
            for value in table_row:
                if value == sample_name:
                    # Generate individual sample page and return link
                    sample_page = html_report_builder.create_sample_html(objs, sample_name, sample_stats, navbar_reports, footer)
                    # Treat sample_name as a link to sample page
                    data = [sample_page, sample_name]
                # If not the sample name, add as an unlinked cell value
                else:
                    data = str(value)
                table_cell_data.append(data)
            sample_pos += 1
            table_row_data.append(table_cell_data)
    else:
        current_app.logger.warning("No stats file '%s'", tsv_outfile_path)

def render_navbar_summary_links(prj, context):
    """
    Render the summary-related links for the navbars in a specific context.
    E.g. for the OG caravel pages or summary page or summary reports pages

    :param looper.Project prj: a project the navbar summary links should be created for
    :param list context: the context for the links
    :return str: html string with the links
    """
    summarizer = Summarizer(prj)
    html_report_builder = HTMLReportBuilder(prj)
    links = html_report_builder.create_navbar_links(objs=summarizer.objs, reports_dir=get_reports_dir(prj),
                                                    stats=summarizer.stats, wd="", caravel=True, context=context)
    return links