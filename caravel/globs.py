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
    global compute_package
    global current_subproj
    global summary_requested
    global run
    global status_check_interval
    global cc

    summarizer = None
    p = None
    selected_project = None
    selected_project_id = None
    log_path = None
    act = None
    compute_config = None
    logging_lvl = None
    summary_links = None
    dests = None
    reset_btn = None
    command = None
    compute_package = None
    current_subproj = None
    summary_requested = None
    run = None
    status_check_interval = None
    cc = None


def purge_project_data():
    """
    Removes project related data while preserving settings/information unassociated with the currently selected project.
    Can be used before new project/subproject initialization.
    """
    global summarizer
    global p
    global selected_project
    global selected_project_id
    global log_path
    global act
    global summary_links
    global dests
    global reset_btn
    global command
    global current_subproj
    global summary_requested
    global run

    summarizer = None
    p = None
    selected_project = None
    selected_project_id = None
    log_path = None
    act = None
    summary_links = None
    dests = None
    reset_btn = None
    command = None
    current_subproj = None
    summary_requested = None
    run = None


