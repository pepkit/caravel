
def init_globals():
    """
    This function initializes global variables, which then can be used in the whole app

    Just need to import globals and then say glob.<variable>
    """
    global summarizer
    global p
    global selected_project
    global log_path
    global act
    global compute_config
    summarizer = None
    p = None
    selected_project = None
    log_path = None
    act = None
    compute_config = None

