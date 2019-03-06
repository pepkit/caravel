""" Package constants """

from divvy.const import COMPUTE_SETTINGS_VARNAME
from looper import __version__ as LOOPER_VERSION
from _version import __version__ as CARAVEL_VERSION

DEFAULT_PORT = 5000
CONFIG_ENV_VAR = "CARAVEL"
CONFIG_PRJ_KEY = "projects"
CONFIG_TOKEN_KEY = "token"
TOKEN_FILE_NAME = ".caravel_token"
TOKEN_LEN = 15
SET_ELSEWHERE = [["--sp"], ["--compute"], ["--env"], ["--help"], ["--version"], ["--selector-attribute"],
                 ["--selector-exclude"], ["--selector-include"], ['']]
LOG_FILENAME = "caravel.log"
from helpers import *  # this import needs to stay at the bottom to prevent the circular dependency problems
REQUIRED_LOOPER_VERSION = get_req_version("looper")
