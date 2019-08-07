""" Package constants """
import os
from divvy.const import COMPUTE_SETTINGS_VARNAME
from looper import __version__ as LOOPER_VERSION
from peppy import __version__ as PEPPY_VERSION
try:
    from geofetch import __version__ as GEOFETCH_VERSION
except ModuleNotFoundError:
    GEOFETCH_VERSION = None
from ._version import __version__ as CARAVEL_VERSION
import ubiquerg


def get_req_version(module=None):
    """
    Read the required version of the specified module from the requirements file

    :param str module: the module to be checked
    :return dict | None: the required version and name of the requested module
    """
    reqs_file = os.path.join(os.path.dirname(__file__),
                             "requirements", "requirements-all.txt")

    if module is not None and os.path.isfile(reqs_file):
        with open(reqs_file) as rf:
            for l in rf:
                try:
                    p, v = l.split("=")
                except ValueError:
                    continue
                if module in p:
                    return {module: v.lstrip("=").rstrip("\n")}
            else:
                raise Exception("Requirement parse failed: {}".
                                format(reqs_file))
    else:
        raise IOError("The requirements file '{rf}' not found or module arg '{mod}' is missing. "
                      "The version of '{mod}' could not be asserted.".format(rf=reqs_file, mod=module))
        return None


DEFAULT_PORT = 5000
DEFAULT_LOGGING_LVL = 20
CONFIG_ENV_VAR = "CARAVEL"
CONFIG_PRJ_KEY = "projects"
CONFIG_TOKEN_KEY = "token"
TOKEN_FILE_NAME = ".caravel_token"
EXAMPLE_FILENAME = "caravel_demo.yaml"
TOKEN_LEN = 15
SET_ELSEWHERE = [["--force-yes"], ["--sp"], ["--env"], ["--help"], ["--version"], ["--selector-attribute"],
                 ["--selector-exclude"], ["--selector-include"], ['--resources'], ['--compute-package'], ['']]
LOG_FILENAME = "caravel.log"
REQUIRED_LOOPER_VERSION = get_req_version("loopercli")["loopercli"]
REQUIRED_PEPPY_VERSION = get_req_version("peppy")["peppy"]
REQUIRED_V_BY_NAME = {"loopercli": REQUIRED_LOOPER_VERSION, "peppy": REQUIRED_PEPPY_VERSION}
V_BY_NAME = {"loopercli": LOOPER_VERSION, "peppy": PEPPY_VERSION, "caravel": CARAVEL_VERSION, "geotetch": GEOFETCH_VERSION}
DEFAULT_TERMINAL_WIDTH = 80
SUMMARY_NAVBAR_PLACEHOLDER = "<li class='nav-item'><a class='nav-link disabled'>No summary yet</a></li>"
TEMPLATES_DIRNAME = "jinja_templates"
TEMPLATES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), TEMPLATES_DIRNAME)
DEMO_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXAMPLE_FILENAME)
COMMAND_KEY = "execute"
POLL_INTERVAL = 3  # in seconds
MISSING_SAMPLE_DATA_TXT = "<code>looper run</code> was called, but not all the samples were correctly processed. " \
                            "</br>Possible reasons: <ul style='padding-left: 30px;'>"\
                            "<li>all jobs are still in a queue</li>" \
                            "<li>submission was not successful</li></ul>"
REQ_CFG_VERSION = 0.2
# this preferences/types can be set in the config file under "preferences" key
PREFERENCES_NAMES_TYPES = {"status_check_interval": int,
                           "compute_package": str}
# mapping of looper.Project metadata of interest and lambda expressions extracting them
PROJECT_MDATA_FUN = {"name": lambda p: p.name,
                     "names_sp": lambda p: ", ".join(p.subprojects.keys()),
                     "num_sp": lambda p: len(p.subprojects.keys()),
                     "num_samples": lambda p: p.num_samples,
                     "protocols": lambda p: ", ".join(sorted(p.protocols)),
                     "inputs_size": lambda p: ubiquerg.filesize_to_str(sum([ubiquerg.size(iput, False)
                                                                           for iput in p.get_inputs()]))}
"""
Config file structure determination 
"""
# config file structure related consts

CFG_NAME = "caravel configuration"
CFG_ENV_VARS = ["CARAVEL"]

CFG_VERSION_KEY = "config_version"
CFG_PROJECTS_KEY = "projects"
CFG_SUBPROJECTS_KEY = "subprojects"
CFG_PREFERENCES_KEY = "preferences"
CFG_PROJECT_NAME_KEY = "name"
CFG_PROJECT_DESC_KEY = "project_description"

CFG_EXAMPLE = """
# example {cfg_name} structure
{version}: 0.2
{preferences}:
  status_check_interval: 2

{projects}:
  /home/johndoe/projects/config_rnaseq.yaml:
    {name}: rnaseq_february
    {desc}: Processes a set of RNA-seq samples 
""".format(cfg_name=CFG_NAME, version=CFG_VERSION_KEY, projects=CFG_PROJECTS_KEY, preferences=CFG_PREFERENCES_KEY,
           name=CFG_PROJECT_NAME_KEY, desc=CFG_PROJECT_DESC_KEY)
