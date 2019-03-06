""" Package constants """

from divvy.const import COMPUTE_SETTINGS_VARNAME
from looper import __version__ as LOOPER_VERSION
from _version import __version__ as CARAVEL_VERSION
import os

def get_req_version(module=None):
    """
    Read the required version of the specified module from the requirements file

    :param str module: the module to be checked
    :return str | None: the required version of the requested module
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
                    return v.lstrip("=").rstrip("\n")
            else:
                raise Exception("Looper requirement parse failed: {}".
                                format(reqs_file))
    else:
        return None


DEFAULT_PORT = 5000
REQUIRED_LOOPER_VERSION = get_req_version("looper")
CONFIG_ENV_VAR = "CARAVEL"
CONFIG_PRJ_KEY = "projects"
CONFIG_TOKEN_KEY = "token"
TOKEN_FILE_NAME = ".caravel_token"
TOKEN_LEN = 15
SET_ELSEWHERE = [["--sp"], ["--compute"], ["--env"], ["--help"], ["--version"], ["--selector-attribute"],
                 ["--selector-exclude"], ["--selector-include"], ['']]
LOG_FILENAME = "caravel.log"