from .const import *


def init_globals():
    """
    This function initializes global variables, which then can be used in the whole app

    Just need to import globals and then say globs.<variable>
    """
    global summarizer
    global p
    global selected_project
    global selected_project_id
    global log_path
    global act
    global compute_config
    global logging_lvl
    global summary_links
    global dests
    global reset_btn
    global command
    global currently_selected_package
    global current_subproj
    global summary_requested
    global run
    global poll_interval

    summarizer = None
    p = None
    selected_project = None
    selected_project_id = None
    log_path = None
    act = None
    compute_config = None
    logging_lvl = DEFAULT_LOGGING_LVL
    summary_links = None
    dests = None
    reset_btn = None
    command = None
    currently_selected_package = None
    current_subproj = None
    summary_requested = None
    run = None
    poll_interval = POLL_INTERVAL


