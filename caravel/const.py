""" Package constants """
import os
from divvy.const import COMPUTE_SETTINGS_VARNAME
from looper import __version__ as LOOPER_VERSION
from peppy import __version__ as PEPPY_VERSION
from ._version import __version__ as CARAVEL_VERSION


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
SET_ELSEWHERE = [["--force-yes"], ["--sp"], ["--compute"], ["--env"], ["--help"], ["--version"],
                 ["--selector-attribute"], ["--selector-exclude"], ["--selector-include"], ['--resources'],
                 ['--compute-package'], ['']]
LOG_FILENAME = "caravel.log"
REQUIRED_LOOPER_VERSION = get_req_version("loopercli")["loopercli"]
REQUIRED_PEPPY_VERSION = get_req_version("peppy")["peppy"]
REQUIRED_V_BY_NAME = {"loopercli": REQUIRED_LOOPER_VERSION, "peppy": REQUIRED_PEPPY_VERSION}
V_BY_NAME = {"loopercli": LOOPER_VERSION, "peppy": PEPPY_VERSION, "caravel": CARAVEL_VERSION}
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

