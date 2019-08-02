""" General-purpose functions """
from __future__ import print_function
import globs
from const import *
from .caravel_conf import *
from .exceptions import MissingCaravelConfigError
import looper
import peppy
import argparse
import random
import string
import fcntl
import termios
import struct
import pandas as _pd
from importlib import import_module
from sys import stderr
from csv import DictReader
from flask import current_app, render_template, redirect, url_for, flash
from re import sub
from functools import partial
from looper.html_reports import *
from looper.looper import Summarizer, get_file_for_project, uniqify, run_custom_summarizers
from logmuse import setup_logger
from looper.utils import fetch_sample_flags
import yacman
from platform import python_version
from distutils.version import LooseVersion
from itertools import chain


def get_items(i, l):
    """
    Get a sublist of list elements by their indices

    :param list[int] i: a list of elements indices
    :param list l: list
    :return list: a list of the desired elements
    """
    return map(l.__getitem__, i)


def get_navbar_summary_links():
    """
    Set the global variable summary_links to the current links HTML string

    :return str: navbar links HTML
    """
    if globs.p is not None and globs.summary_requested:
        reports_dir = get_reports_dir(globs.p)
        context = ["summary", os.path.basename(reports_dir)]
        globs.summary_links = render_navbar_summary_links(globs.p, wd=reports_dir, context=context) \
            if check_for_summary(globs.p) else SUMMARY_NAVBAR_PLACEHOLDER
    else:
        globs.summary_links = ""


def compile_results_content(log_path, act):
    """
    Compile the content of the looper results page. Apart from reading the contents of the log file
    (that stores the looper log) a header and a footer are pre/appended.

    :param str log_path: a path to the caravel log file to be shown
    :param str act: the name of the action to be shown in the header of the page
    :return str: the page
    """
    log_wrpr = "<h2><code>looper {act} </code>results:</br></h2><hr>{content}<hr>log read from <code>{path}</code></br>"
    try:
        with open(log_path, "r") as log:
            log_content = log.read()
            compiled_text = log_wrpr.format(act=act, content=log_content, path=log_path)
    except IOError:
        compiled_text = "<b>Cannot find the log file: '{}'</b>".format(log_path)
    return _color_to_bold(compiled_text)


def _color_to_bold(txt):
    """
    Replace the color markers (from colorama.Fore) with the HTML bold tags

    :param txt: the string to be edited
    :return str: the uncolored and bolded string
    """
    return sub(pattern=r"\[\d{1}[a-z]{1}", repl="</b>", string=sub(pattern=r"\[\d{2}[a-z]{1}", repl="<b>", string=txt))


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


def _ensure_package_installed(name, error_msg_appdx=""):
    """
    Current demonstrational pipeline is a pypiper pipeline.
    Therefore we need to ensure pypiper can be imported when caravel is launched in the demo mode.
    This function can be used to perform such an assurance

    :param str name: package name to be tested
    :param str error_msg_appdx: string to be appended to the error message
        (provides more detail as to why the package is conditionally requred)
    """
    try:
        import_module(name)
        current_app.logger.debug("'{}' imported successfully".format(name))
    except ImportError:
        raise ImportError("Package '{}' could not be imported, "
                          "but is conditionally required. {}".format(name, error_msg_appdx))


def select_config(config_filepath=None,
                  config_env_vars=None,
                  default_config_filepath=None,
                  check_exist=True,
                  on_missing=lambda fp: IOError(fp)):
    """
    Selects the config file to load.

    This uses a priority ordering to first choose a config filepath if it's given,
    but if not, then look in a priority list of environment variables and choose
    the first available filepath to return.

    :param str | NoneType config_filepath: direct filepath specification
    :param Iterable[str] | NoneType config_env_vars: names of environment
        variables to try for config filepaths
    :param str default_config_filepath: default value if no other alternative
        resolution succeeds
    :param bool check_exist: whether to check for path existence as file
    :param function(str) -> object on_missing: what to do with a filepath if it
        doesn't exist
    """
    def _checker(path, strict=check_exist, user_error=on_missing):
        if path:
            if not strict or os.path.isfile(path):
                return path
            current_app.logger.error(path)
            result = user_error(path)
            if isinstance(result, Exception):
                raise result
            return result
    try:
        env_var = yacman.get_first_env_var(config_env_vars)[1] if config_env_vars else config_env_vars
    except TypeError:
        env_var = None
    paths = [config_filepath,
             env_var,
             default_config_filepath]
    msgs = ["{} config_filepath {}",
            "{} environment variable {}",
            "{} default config file {}"]
    i = 0
    current_app.logger.debug(msgs[i].format("Checking", paths[i]))
    try:
        while _checker(paths[i]) is None:
            i += 1
            current_app.logger.debug(msgs[i].format("Checking", paths[i]))
        current_app.logger.info(msgs[i].format("Using", "-- " + paths[i]))
        return paths[i]
    except IndexError:
        txt = "No configuration file found"
        result = on_missing(txt)
        if isinstance(result, Exception):
            raise result
        print(txt)


def parse_config_file():
    """
    Path to the PEP projects and predefined token are extracted if file is read successfully.
    Additionally, looks for a custom command to execute.

    :return CaravelConf: a configuration object
    """
    cfg_path = current_app.config.get("project_configs")
    if current_app.config.get("demo"):
        _ensure_package_installed("pypiper", "The demonstrational pipeline requires this package. "
                                             "Install 'pypiper' using: pip install piper")
        current_app.logger.info("Demo mode, the project configs list is auto-populated with example data")
        cfg_path = DEMO_FILE_PATH
    project_list_path = select_config(config_filepath=cfg_path, config_env_vars=CONFIG_ENV_VAR,
                                      on_missing=lambda fp: MissingCaravelConfigError(fp))
    return CaravelConf(project_list_path)


def select_project(proj_selection_str):
    """
    Parse the string returned by the index page form. Three strings separated by a semicolon are expected by default.
    If the last one (subproject in our use case) is missing, an empty list is appended to the returned list,
    which is subsequently disregarded by looper.Project.__init__ and no subproject is activated

    :param str proj_selection_str: a string formatted like: "<project_path>;<project_id>;<subproject_name>"
    :return list[str]: separated project, ID and subproject name
    """

    if globs.selected_project is None and proj_selection_str is None:
        raise TypeError("No selection provided")
    else:
        if None not in (proj_selection_str, globs.selected_project) and globs.selected_project != proj_selection_str:
            globs.purge_project_data()
            globs.summary_links = SUMMARY_NAVBAR_PLACEHOLDER
            current_app.logger.info("Project data removed")
    try:
        seletion_list = proj_selection_str.split(";")
        return seletion_list if len(seletion_list) > 2 else seletion_list + [list()]
    except AttributeError:
        current_app.logger.debug("The project was not selected, recovering previous one")
        return globs.selected_project, globs.selected_project_id, globs.current_subproj


def write_preferences(preferences_dict):
    """
    Write the preferences to the global caravel config file

    :param dict preferences_dict: preferences to be written
    """
    for preference_name, preference_value in preferences_dict.items():
        try:
            if check_insert_data(preference_value, PREFERENCES_NAMES_TYPES[preference_name], preference_name):
                globs.cc.setdefault(CFG_PREFERENCES_KEY, dict())
                globs.cc[CFG_PREFERENCES_KEY][preference_name] = preference_value
        except KeyError:
            current_app.logger.warning("Preference '{}' cannot be set. The defined preferences are: {}".
                                       format(preference_name, ", ".join(PREFERENCES_NAMES_TYPES.keys())))
    globs.cc.write()


def read_preferences():
    """
    Update preferences. If an appropriate key under preferences key is found, the type of the value
    associated with the key is checked and the particular setting was not set manually -- the global setting is updated.
    If the criteria are not met, the settings will be disregarded.
    """

    def _check_apply_pref(cc, name, value_type):
        """
        Check the preference update possibility and perform it

        :param CaravelConf cc: caravel preferences object
        :param str name: name of the preference to be updated
        :param value_type: class of the value to be set
        """
        if getattr(globs, name, False) is None and hasattr(cc[CFG_PREFERENCES_KEY], name) and \
                check_insert_data(cc[CFG_PREFERENCES_KEY][name], value_type, name):
            setattr(globs, name, cc[CFG_PREFERENCES_KEY][name])
            current_app.logger.debug("'{}' set to {}".format(name, cc[CFG_PREFERENCES_KEY][name]))

    if hasattr(globs.cc, CFG_PREFERENCES_KEY):
        current_app.logger.debug("cc has the pref key")
        for pref_name, val_type in PREFERENCES_NAMES_TYPES.iteritems():
            _check_apply_pref(globs.cc, pref_name, val_type)


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
            raise ImportError("The version of {name} in use ({in_use}) does not meet the caravel requirement "
                              "({req})".format(name=package, in_use=current[package], req=required[package]))
    return True


def eprint(*args, **kwargs):
    """
    Print the provided text to stderr.
    """
    print(*args, file=stderr, **kwargs)


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


def _get_sp_txt(p):
    """
    Produces a comma separated string of the defined subproject names, if avaialble

    :param looper.Project p: project to search the subprojects in
    :return str | NoneType: subprojects names
    """
    try:
        sp_names = p.subprojects.keys()
    except AttributeError:
        sp_names = None
    return ",".join(sp_names) if sp_names is not None else sp_names


def project_info_dict(p):
    """
    Composes a simple dictionary used to display the project information
    :param looper.Project p: project that the info should be based on
    :return dict: dictionary with project information
    """
    return {"name": p.name, "config_file": p.config_file, "sample_count": p.num_samples,
             "output_dir": p.metadata.output_dir, "subprojects": _get_sp_txt(globs.p)}


def random_string(n):
    """
    Generates a random string of length N

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

        self.add_argument(
            "--demo",
            action="store_true",
            dest="demo",
            help="Run caravel with demo data.")

    def format_help(self):
        """ Add version information to help text. """
        return _version_text() + super(CaravelParser, self).format_help()


def _version_text():
    """
    Compile a string for the argparser help with caravel and looper versions

    :return str: a compiled string
    """
    return "caravel version: {cv}\nlooper version: {lv}\n".format(cv=V_BY_NAME["caravel"], lv=V_BY_NAME["loopercli"])


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
    eprint(filler + spaced_txt + filler)


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
    setup_logger("looper", level=logging_lvl, stream=stderr, logfile=log_path, plain_format=True)
    eprint("\nAction: {}\n".format(act))
    # run selected looper action
    with peppy.ProjectContext(prj) as prj:
        if act in ["run", "rerun"]:
            run = looper.looper.Runner(prj)
            try:
                run(args, None, rerun=(act == "rerun"))
                globs.run = True
            except IOError:
                raise Exception("{} pipelines_dir: '{}'".format(prj.__class__.__name__, prj.metadata.pipelines_dir))
        if act == "destroy":
            globs.run = False
            return looper.looper.Destroyer(prj)(args, False)
        if act == "summarize":
            globs.summary_requested = True
            run_custom_summarizers(prj)
            _render_summary_pages(prj)
        if act == "check":
            looper.looper.Checker(prj)(flags=args.flags)

        if act == "clean":
            return looper.looper.Cleaner(prj)(args, False)


def _render_summary_pages(prj):
    """
    Render the summary pages with caravel navbars and footers

    :param looper.Project prj: a project the summary pages should be create for
    :return:
    """
    rep_dir = os.path.basename(get_reports_dir(prj))
    # instantiate the objects needed fot he creation the pages
    j_env = get_jinja_env(TEMPLATES_PATH)
    html_report_builder = HTMLReportBuilder(prj)
    globs.summarizer = Summarizer(prj)
    objs = globs.summarizer.objs
    stats = globs.summarizer.stats
    columns = globs.summarizer.columns
    # create navbar links
    links_summary = render_navbar_summary_links(prj, wd=html_report_builder.reports_dir, context=[rep_dir])
    links_reports = render_navbar_summary_links(prj, wd=html_report_builder.reports_dir)
    # create navbars
    navbar_summary = render_jinja_template("navbar.html", j_env, dict(summary_links=links_summary))
    navbar_reports = render_jinja_template("navbar.html", j_env, dict(summary_links=links_reports))
    # create footer
    footer_vars = dict(caravel_version=CARAVEL_VERSION, looper_version=LOOPER_VERSION, python_version=python_version(),
                       login=current_app.config["login"])
    footer = render_jinja_template("footer.html", j_env, footer_vars)
    html_report_builder.create_index_html(objs, stats, columns, navbar=navbar_summary, navbar_reports=navbar_reports,
                                          footer=footer)


def use_existing_stats_objs(prj):
    """
    Check for existence of the 'stats_summary.tsv' and 'objs_summary.tsv' -- files needed for
    the creation of the summary pages. Additionally get the unique summary columns for the project.

    Return the contents or None if one of them does not exist.
    :param looper.Projct prj: the project that the files should be checked for
    :return (list, pandas.DataFrame, list): a pair of read files
    """
    stats_path = get_file_for_project(prj, "stats_summary.tsv")
    objs_path = get_file_for_project(prj, "objs_summary.tsv")
    warn_msg = "Could not read file: '{}'. Creating new '" + stats_path + "' and '" + objs_path + "'"
    if not all([os.path.isfile(f) for f in [stats_path, objs_path]]):
        current_app.logger.debug("'{}' and/or '{}' is missing. Creating new ones...".format(stats_path, objs_path))
        return None
    current_app.logger.debug("Both '{}' and '{}' exist".format(stats_path, objs_path))
    try:
        objs = _pd.read_csv(objs_path, sep="\t", index_col=0)
    except Exception as e:
        current_app.logger.debug(e)
        current_app.logger.warning(warn_msg.format(objs_path))
        return None
    stats = []
    try:
        with open(stats_path) as f:
            reader = DictReader(f, delimiter="\t")
            for row in reader:
                stats.append(row)
    except Exception as e:
        current_app.logger.debug(e)
        current_app.logger.warning(warn_msg.format(stats_path))
        return None
    columns = uniqify(flatten([list(i.keys()) for i in stats]))
    return stats, objs, columns


def render_navbar_summary_links(prj, wd, context=None):
    """
    Render the summary-related links for the navbars in a specific context.
    E.g. for the OG caravel pages or summary page or summary reports pages

    :param looper.Project prj: a project the navbar summary links should be created for
    :param list[str] context: the context for the links
    :return str: html string with the links
    """
    context = context or list()
    html_report_builder = HTMLReportBuilder(prj)
    data = use_existing_stats_objs(prj)
    if data is not None:
        stats, objs, _ = data
    else:
        globs.summarizer = Summarizer(prj)
        objs = globs.summarizer.objs
        stats = globs.summarizer.stats
    args = dict(objs=objs, stats=stats, wd=wd, context=context, include_status=False)
    links = html_report_builder.create_navbar_links(**args)
    return links


def get_sample_flags(p, samples=None):
    """
    Get samples status dict for the selected sample names.
    If no samples are specified, flags for all will be searched for.

    :param looper.Project p: project object
    :param dict samples: successfully submitted samples
    :return dict: a dictionary of sample names and the corresponding flags
    """
    samples = samples or list(p.sample_names)
    return None if p is None else {s: fetch_sample_flags(p, s) for s in samples}


def check_if_run(p):
    """
    Check whether the project has been run based on existence of any flag among all samples

    :param looper.Project p: project object
    :return bool: a logical indicating whether the pipeline was run on any of the samples
    """
    return not all(value == [] for value in get_sample_flags(p).values())


def sample_info_hint(p):
    """
    Based on the summary files existence return the hint how to get the more sample-specific information

    :param looper.Project p: project object
    :return str: a HTML formatted info
    """
    rep_dir = get_reports_dir(p)
    samples_path = os.path.join(rep_dir, "samples.html")
    msg = "<hr><small>To get sample-specific log files {}</small>"
    insert = "see <a href='../summary/{}/samples.html'>samples summary page</a>".format(os.path.basename(rep_dir)) \
        if (check_for_summary(p) and os.path.isfile(samples_path)) else "run <code>looper summarize</code>"
    return msg.format(insert)
