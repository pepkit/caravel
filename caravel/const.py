""" Package constants """

from peppy import COMPUTE_SETTINGS_VARNAME
from looper import __version__ as looper_version
LOOPER_VERSION = looper_version
REQUIRED_LOOPER_VERSION = "0.11.0"
CONFIG_ENV_VAR = "CARAVEL"
CONFIG_PRJ_KEY = "projects"
CONFIG_TOKEN_KEY = "token"
TOKEN_FILE_NAME = ".caravel_token"
TOKEN_LEN = 15
SET_ELSEWHERE = [["--sp"], ["--compute"], ["--env"], ["--help"], ["--version"], ["--selector-attribute"],
                 ["--selector-exclude"], ["--selector-include"], ['']]
LOG_FILENAME = "caravel.log"

