""" Main UI application for using looper """

from functools import wraps
import logging
import traceback
import warnings
from flask import Blueprint, Flask, render_template, request, jsonify, session, redirect, send_from_directory, url_for,\
    flash
import yaml
from const import *
from helpers import *
from looper_parser import *
import divvy
from textile import textile
from peppy.utils import coll_like
from platform import python_version
from looper.project import Project
from looper.html_reports import *


app = Flask(__name__, template_folder=TEMPLATES_PATH)
app.logger.info("Using python {}".format(python_version()))


@app.context_processor
def inject_dict_for_all_templates():
    global summary_links
    try:
        summary_links
    except NameError:
        summary_links = SUMMARY_NAVBAR_PLACEHOLDER
    return dict(caravel_version=CARAVEL_VERSION, looper_version=LOOPER_VERSION, python_version=python_version(),
                referrer=request.referrer, debug=app.config["DEBUG"], summary_links=summary_links)


def clear_session_data(keys):
    """
    Removes the non default data (created in the app lifetime) from the flask.session object.
    :param keys: a list of keys to be removed from the session
    """
    if not coll_like(keys):
        raise TypeError("Keys to clear must be collection-like; "
                        "got {}".format(type(keys)))
    for key in keys:
        try:
            session.pop(key, None)
        except KeyError:
            app.logger.info("{k} not found in the session".format(k=key))


def generate_token(token=None, n=TOKEN_LEN):
    """
    Set global app variable login token.

    If token provided, use its value. Print info to the terminal

    :param token: the token to use
    :param n: length of the token to generate
    """
    global login_token
    login_token = token or random_string(n)
    eprint("\nCaravel is protected with a token.\nCopy this link to your browser to authenticate:\n")
    geprint("http://localhost:{port}/?token={token}".format(port=app.config.get("port"), token=login_token) + "\n")


def token_required(func):
    """
    This decorator checks for a token, verifies if it is valid and redirects to the login page if needed

    :param callable func: function to be decorated
    :return callable: decorated function
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        global login_token
        if not app.config["DEBUG"]:
            url_token = request.args.get('token')
            if url_token is not None:
                app.logger.info("Using token from the URL argument")
                if url_token == login_token:
                    session["token"] = url_token
                else:
                    return render_error_msg("Invalid token")
            else:
                try:
                    session["token"]
                except KeyError:
                    try:
                        login_token
                    except NameError:
                        return render_error_msg("No login token and session token found.")
                    else:
                        return render_error_msg("Other instance of caravel is running elsewhere."
                                                " Log in using the URL printed to the terminal when it was started.")
                else:
                    app.logger.info("Using the token from the session")
                    if session["token"] != login_token:
                        return render_error_msg("Invalid token")

        return func(*args, **kwargs)
    return decorated


@token_required
def shutdown_server():
    shut_func = request.environ.get('werkzeug.server.shutdown')
    if shut_func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    app.logger.info("Shutting down...")
    clear_session_data(keys=['token', '_csrf_token'])
    shut_func()


def generate_csrf_token(n=100):
    """
    Generate a CSRF token
    :param n: length of a token
    :return flask.session: a session object with "_csrf_token_key"
    """
    if '_csrf_token' not in session:
        session['_csrf_token'] = random_string(n)
        app.logger.info("CSRF token generated")
    else:
        app.logger.info("CSRF token retrieved from the session")
    return session['_csrf_token']


app.jinja_env.globals['csrf_token'] = generate_csrf_token


@app.errorhandler(Exception)
def unhandled_exception(e):
    app.logger.error('Unhandled Exception: %s', (e))
    eprint(traceback.format_exc())
    return render_template('error.html', e=[e], types=[e.__class__.__name__]), 500


@app.route('/shutdown', methods=['GET'])
@token_required
def shutdown():
    shutdown_server()
    return 'Server was shut down successfully'


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token_csrf = session['_csrf_token']
        token_get_csrf = request.form.get("_csrf_token")
        if not token_csrf or token_csrf != token_get_csrf:
            return render_error_msg("The CSRF token is invalid")


def parse_config_file():
    """
    Parses the config file (YAML) provided as an CLI argument or in a environment variable ($CARAVEL).

    The CLI argument is given the priority.
    Path to the PEP projects and predefined token are extracted if file is read successfully.

    :return list[str]: project list
    """

    project_list_path = app.config.get("project_configs") or os.getenv(CONFIG_ENV_VAR)
    if project_list_path is None:
        raise ValueError("Please set the environment variable {} or provide a YAML file listing paths to project "
                         "config files".format(CONFIG_ENV_VAR))
    project_list_path = os.path.normpath(os.path.join(os.getcwd(), os.path.expanduser(project_list_path)))
    if not os.path.isfile(project_list_path):
        raise ValueError("Project configs list isn't a file: {}".format(project_list_path))
    with open(project_list_path, 'r') as stream:
        pl = yaml.safe_load(stream)
        assert CONFIG_PRJ_KEY in pl, \
            "'{}' key not in the projects list file.".format(CONFIG_PRJ_KEY)
        projects = pl[CONFIG_PRJ_KEY]
        # for each project use the dirname of the yaml file to establish the paths to the project itself,
        # additionally expand the environment variables and the user
        projects = sorted(flatten([glob_if_exists(os.path.join(
            os.path.dirname(project_list_path), os.path.expanduser(os.path.expandvars(prj)))) for prj in projects]))
    return projects


def parse_token_file(path=TOKEN_FILE_NAME):
    """
    Get the token from the hidden dotfile

    :param str path: path to the file to be parsed. If not provided, the `TOKEN_FILE_NAME` will be used
    :return str: the token
    """
    try:
        with open(path, 'r') as stream:
            out = yaml.safe_load(stream)
        assert CONFIG_TOKEN_KEY in out, \
            "'{token}' key not in the {file} file.".format(token=CONFIG_TOKEN_KEY, file=TOKEN_FILE_NAME)
        token = out[CONFIG_TOKEN_KEY]
        token_unique_len = len(''.join(set(token)))
        if token_unique_len < 5:
            app.logger.warning("The predefined authentication token in the config file has to be composed of at least 5"
                               " unique characters, got {len} in '{token}'.".format(len=token_unique_len, token=token))
            app.logger.info("Using randomly generated token.")
            token = None
        else:
            app.logger.info("{} file found, using the predefined token".format(TOKEN_FILE_NAME))
    except IOError:
        token = None
    return token


# Routes
@app.route("/")
@app.route("/index")
@token_required
def index():
    global projects
    global p
    global selected_project
    global reset_btn
    global summary_links
    try:
        reset_btn
    except NameError:
        reset_btn = None
    if request.args.get('reset'):
        summary_links = SUMMARY_NAVBAR_PLACEHOLDER
        try:
            del selected_project
        except NameError:
            app.logger.info("No project selected yet")
        try:
            del p
            app.logger.info("Project data removed")
        except NameError:
            app.logger.info("No project defined yet")
        reset_btn = None
    app.logger.info("reset button: {}".format(str(reset_btn)))
    projects = parse_config_file()
    return render_template('index.html', projects=projects, reset_btn=reset_btn)


@app.route("/set_comp_env")
@token_required
def set_comp_env():
    global compute_config
    global active_settings
    global currently_selected_package
    try:
        compute_config
    except NameError:
        compute_config = divvy.ComputingConfiguration()
    selected_package = request.args.get('compute', type=str)
    try:
        currently_selected_package
    except NameError:
        currently_selected_package = "default"
    if selected_package is not None:
        success = compute_config.clean_start(selected_package)
        if not success:
            msg = "Compute package '{}' cannot be activated".format(selected_package)
            app.logger.warning(msg)
            return jsonify(active_settings=render_template('compute_info.html', active_settings=None, msg=msg))
        currently_selected_package = selected_package
        active_settings = compute_config.get_active_package()
        return jsonify(active_settings=render_template('compute_info.html', active_settings=active_settings))
    active_settings = compute_config.get_active_package()
    notify_not_set = COMPUTE_SETTINGS_VARNAME[0] if compute_config.default_config_file == compute_config.config_file\
        else None
    return render_template('set_comp_env.html', env_conf_file=compute_config.config_file,
                           compute_packages=compute_config.list_compute_packages(), active_settings=active_settings,
                           currently_selected_package=currently_selected_package, notify_not_set=notify_not_set)


@app.route("/process", methods=['GET', 'POST'])
@token_required
def process():
    global p
    global config_file
    global p_info
    global selected_project
    global projects
    global reset_btn
    reset_btn = True
    from looper import build_parser as blp

    actions = get_positional_args(blp(), sort=True)

    # this try-except block is used to determine whether the user should be redirected to the index page
    # to select the project when they land on the process subpage from the set_comp_env subpage
    try:
        selected_project
    except NameError:
        selected_project = request.form.get('select_project')
        if selected_project is None:
            app.logger.info("The project is not selected, redirecting to the index page.")
            flash("No project was selected, choose one from the list below.")
            del selected_project
            return redirect(url_for('index'))
    else:
        new_selected_project = request.form.get('select_project')
        if new_selected_project is not None and selected_project != new_selected_project:
            selected_project = new_selected_project
    config_file = str(os.path.expandvars(os.path.expanduser(selected_project)))
    try:
        p
    except NameError:
        p = Project(config_file)
    try:
        subprojects = list(p.subprojects.keys())
    except AttributeError:
        subprojects = None
    # TODO: p_info will be removed altogether in the future version
    p_info = {
        "name": p.name,
        "config_file": p.config_file,
        "sample_count": p.num_samples,
        "output_dir": p.metadata.output_dir,
        "subprojects": subprojects
    }
    return render_template('process.html', p_info=p_info, change=None, selected_subproject=p.subproject, actions=actions)


@app.route('/_background_subproject')
def background_subproject():
    global p
    global config_file
    sp = request.args.get('sp', type=str)
    output = "Activated subproject: " + sp
    if sp == "None":
        p.deactivate_subproject()
    else:
        p.activate_subproject(sp)
    return jsonify(subproj_txt=output, sample_count=p.num_samples)


@app.route('/_background_options')
def background_options():
    global p_info
    global act
    global dests
    global p
    from looper.looper import build_parser as blp
    act = request.args.get('act', type=str) or "run"
    parser_looper = blp()
    form_elements_data = get_form_elements_data(parser_looper, p, act)
    dests = form_elements_data[2]
    grouped_data = form_elements_data_by_type(form_elements_data)
    return jsonify(options=render_template('options.html', grouped_form_data=grouped_data))


@app.route('/summary', methods=['GET'])
def summary():
    global p
    global selected_project
    try:
        selected_project
    except NameError:
        app.logger.info("The project is not selected, redirecting to the index page.")
        flash("No project was selected, choose one from the list below.")
        return redirect(url_for('index'))
    summary_html_name = get_summary_html_name(p)
    summary_location = os.path.join(p.metadata.output_dir, summary_html_name)
    if os.path.exists(summary_location):
        summary_string = "summary/{}".format(summary_html_name)
        return redirect(summary_string)
    else:
        flash("Summary hasn't been generated yet")
        app.logger.warning("Summary file '{file}' not found in '{dir}'".format(file=summary_html_name,
                                                                           dir=os.path.dirname(summary_location)))
        return redirect(request.referrer)


@app.route("/summary/<path:filename>", methods=['GET'])
def serve_static(filename):
    global p
    return send_from_directory(p.output_dir, filename)


@app.route("/action", methods=['GET', 'POST'])
@token_required
def action():
    global act
    global config_file
    global dests
    global currently_selected_package
    global log_path
    global logging_lvl
    global p
    global summary_links
    args = argparse.Namespace()
    args_dict = vars(args)
    # Set the arguments from the forms
    for arg in dests:
        value = convert_value(request.form.get(arg))
        args_dict[arg] = value
    # hardcode upfront confirmation in the yes/no query; used in clean and destroy actions
    args_dict["force_yes"] = True
    # perform necessary changes so the looper understands the Namespace
    args_dict = parse_namespace(args_dict)
    # establish the looper log path
    log_path = os.path.join(p.output_dir, LOG_FILENAME)
    # set the selected computing environment in the Project object
    try:
        p.dcc.activate_package(currently_selected_package)
    except NameError:
        app.logger.info("The compute package was not selected, using 'default'.")
        p.dcc.activate_package("default")
    # run looper action
    run_looper(prj=p, args=args, act=act, log_path=log_path, logging_lvl=logging_lvl)
    # TODO: will be changed
    s = Summarizer(p)
    hrb = HTMLReportBuilder(p)
    summary_links = hrb.create_navbar_links(objs=s.objs, reports_dir=get_reports_dir(p), stats=s.stats, wd="",caravel=True)
    return render_template("/execute.html")


@app.route('/_background_result')
def background_result():
    global p_info
    global log_path
    global act
    page = compile_results_content(log_path, act)
    return jsonify(result=textile(page))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'caravel.ico', mimetype='image/vnd.microsoft.icon')


def main():
    global logging_lvl
    ensure_version()
    parser = CaravelParser()
    args = parser.parse_args()
    app.config["port"] = args.port
    app.config["project_configs"] = args.config
    app.config["DEBUG"] = args.debug
    app.config['SECRET_KEY'] = 'thisisthesecretkey'
    if app.config["DEBUG"]:
        warnings.warn("You have entered the debug mode. The server-client connection is not secure!")
        logging_lvl = 10
    else:
        logging_lvl = DEFAULT_LOGGING_LVL
        generate_token(token=parse_token_file())
    logging.getLogger().setLevel(logging_lvl)
    app.run(port=args.port)


if __name__ == "__main__":
    main()
