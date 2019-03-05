""" Package constants """

import os
from divvy.const import COMPUTE_SETTINGS_VARNAME
from looper import __version__ as looper_version


def _get_looper_req():
    reqs_file = os.path.join(os.path.dirname(__file__),
                             "requirements", "requirements-all.txt")
    if os.path.isfile(reqs_file):
        with open(reqs_file) as rf:
            for l in rf:
                try:
                    p, v = l.split("=")
                except ValueError:
                    continue
                if "looper" in p:
                    return v.lstrip("=").rstrip("\n")
            else:
                raise Exception("Looper requirement parse failed: {}".
                                format(reqs_file))
    else:
        return None


LOOPER_VERSION = looper_version
REQUIRED_LOOPER_VERSION = _get_looper_req()
CONFIG_ENV_VAR = "CARAVEL"
CONFIG_PRJ_KEY = "projects"
CONFIG_TOKEN_KEY = "token"
TOKEN_FILE_NAME = ".caravel_token"
TOKEN_LEN = 15
SET_ELSEWHERE = [["--sp"], ["--compute"], ["--env"], ["--help"], ["--version"], ["--selector-attribute"],
                 ["--selector-exclude"], ["--selector-include"], ['']]
LOG_FILENAME = "caravel.log"
