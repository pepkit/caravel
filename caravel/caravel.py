""" Main UI application for using looper """

from functools import wraps
import getpass
import traceback
import warnings
from flask import Flask, render_template, request, jsonify, session, redirect, send_from_directory, url_for, flash
import globs
from .const import *
from .helpers import *
from .looper_parser import *
import divvy
from textile import textile
from platform import python_version
from looper.project import Project
from looper.html_reports import *
from ubiquerg import is_collection_like


app = Flask(__name__, template_folder=TEMPLATES_PATH)


def clear_session_data(keys):
    """
    Removes the non default data (created in the app lifetime) from the flask.session object.
    :param keys: a list of keys to be removed from the session
    """
    if not is_collection_like(keys):
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
                        return render_error_msg("Log in using the URL printed to the terminal when it was started.")
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


@app.after_request
def add_header(r):
    """
    Add headers to force the browser not to cache the pages

    This is relevant for serving the summary pages for multiple projects one after another
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers["Cache-Control"] = 'public, max-age=0'
    return r


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
        token = out[CONFIG_TOKEN_KEY][0]
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


def gdsv(s):
    """
    Get default slider value (gdsv)

    Custom filter for jinja environment. Extracts default value from string returned by looper custom types

    :param str s: string with default value encoded by "value=<number>". Like "min=1 max=430 step=1 value=430"
    :return str: default value
    """
    try:
        lst = s.split(' ')
        value_idx = [x.startswith("value") for x in lst].index(True)
        value_string = lst[value_idx]
        result = value_string.split("=")[1]
    except Exception as e:
        app.logger.warning("Got '{}'; could not determine default option for slider out of string: '{}'."
                           " Returning 'None' instead".format(e.__class__.__name__, s))
        result = None
    return result


@app.context_processor
def inject_dict_for_all_templates():
    if globs.summary_links is None:
        globs.summary_links = SUMMARY_NAVBAR_PLACEHOLDER
    return dict(caravel_version=CARAVEL_VERSION, looper_version=LOOPER_VERSION, python_version=python_version(),
                referrer=request.referrer, debug=app.config["DEBUG"], summary_links=globs.summary_links,
                login=app.config['login'])


app.jinja_env.filters['gdsv'] = gdsv
app.jinja_env.globals['csrf_token'] = generate_csrf_token


# Routes
@app.route("/")
@app.route("/index")
@token_required
def index():
    get_navbar_summary_links()
    if request.args.get('reset'):
        globs.init_globals()
        globs.summary_links = SUMMARY_NAVBAR_PLACEHOLDER
        globs.reset_btn = None
        app.logger.info("Project data removed")
    projects, globs.command = parse_config_file()
    return render_template('index.html', projects=projects, reset_btn=globs.reset_btn, command_btn=globs.command,
                           selected=globs.selected_project, selected_id=globs.selected_project_id)


@app.route('/_background_exec')
def background_exec():
    import subprocess
    # get command to execute, if it's None it means the select was not used which means that there's only one option
    cmd = request.args.get('cmd', type=str) or globs.command
    out = subprocess.call(cmd, shell=True)
    return jsonify(exec_txt=out)


@app.route("/preferences")
@token_required
def set_comp_env():
    global active_settings
    if globs.compute_config is None:
        globs.compute_config = divvy.ComputingConfiguration()
    selected_package = request.args.get('compute', type=str)
    selected_interval = request.args.get('interval', type=int) or globs.poll_interval
    globs.poll_interval = int(selected_interval)
    if globs.currently_selected_package is None:
        globs.currently_selected_package = "default"
    if selected_package is not None:
        success = globs.compute_config.clean_start(selected_package)
        if not success:
            msg = "Compute package '{}' cannot be activated".format(selected_package)
            app.logger.warning(msg)
            return jsonify(active_settings=render_template('compute_info.html', active_settings=None, msg=msg))
        globs.currently_selected_package = selected_package
        active_settings = globs.compute_config.get_active_package()
        return jsonify(active_settings=render_template('compute_info.html', active_settings=active_settings))
    active_settings = globs.compute_config.get_active_package()
    notify_not_set = COMPUTE_SETTINGS_VARNAME[0] if \
        globs.compute_config.default_config_file == globs.compute_config.config_file else None

    return render_template('preferences.html', env_conf_file=globs.compute_config.config_file,
                           compute_packages=globs.compute_config.list_compute_packages(), active_settings=active_settings,
                           currently_selected_package=globs.currently_selected_package, notify_not_set=notify_not_set,
                           default_interval=globs.poll_interval)


@app.route("/process", methods=['GET', 'POST'])
@token_required
def process():
    from looper import build_parser as blp
    actions = get_positional_args(blp(), sort=True)
    # this try-except block is used to determine whether the user should be redirected to the index page
    # to select the project when they land on the process subpage from the set_comp_env subpage
    if globs.selected_project is None and request.form.get('select_project') is None:
        app.logger.info("The project is not selected, redirecting to the index page.")
        flash("No project was selected, choose one from the list below.")
        return redirect(url_for('index'))
    else:
        new_selected_project = request.form.get('select_project')
        if new_selected_project is not None and globs.selected_project != new_selected_project:
            globs.selected_project = parse_selected_project(new_selected_project)[0]
            globs.selected_project_id = parse_selected_project(new_selected_project)[1]
            app.logger.debug("Selected project path: " + globs.selected_project)
            app.logger.debug("Selected project id: " + globs.selected_project_id)
    config_file = str(os.path.expandvars(os.path.expanduser(globs.selected_project)))
    if globs.p is None:
        globs.p = Project(config_file)
    try:
        subprojects = globs.p.subprojects.keys()
    except AttributeError:
        subprojects = None
    get_navbar_summary_links()
    globs.reset_btn = True
    return render_template('process.html', p_info=project_info_dict(globs.p), change=None,
                           selected_subproject=globs.p.subproject, actions=actions, subprojects=subprojects,
                           interval=globs.poll_interval)


@app.route('/_background_subproject')
def background_subproject():
    sp = request.args.get('sp', type=str)
    output = "Activated subproject: " + sp
    if sp == "None":
        globs.p.deactivate_subproject()
    else:
        globs.p.activate_subproject(sp)
        globs.run = False
    globs.summary_requested = None
    get_navbar_summary_links()
    return jsonify(subproj_txt=output, p_info=project_info_dict(globs.p), navbar_links=globs.summary_links)


@app.route('/_background_options')
def background_options():
    from looper.looper import build_parser as blp
    globs.act = request.args.get('act', type=str) or "run"
    parser_looper = blp()
    form_elements_data = get_form_elements_data(parser_looper, globs.p, globs.act)
    globs.dests = form_elements_data[2]
    grouped_data = form_elements_data_by_type(form_elements_data)
    return jsonify(options=render_template('options.html', grouped_form_data=grouped_data))


@app.route('/summary', methods=['GET'])
@token_required
def summary():
    globs.summary_requested = True
    if globs.selected_project is None:
        app.logger.info("The project is not selected, redirecting to the index page.")
        flash("No project was selected, choose one from the list below.")
        return redirect(url_for('index'))
    summary_html_name = get_summary_html_name(globs.p)
    summary_location = os.path.join(globs.p.metadata.output_dir, summary_html_name)
    if check_for_summary(globs.p):
        summary_string = "summary/{}".format(summary_html_name)
        return redirect(summary_string)
    else:
        flash("Summary hasn't been generated yet")
        app.logger.warning("Summary file '{file}' not found in '{dir}'".format(file=summary_html_name,
                                                                           dir=os.path.dirname(summary_location)))
        return redirect(request.referrer)


@app.route("/summary/<path:filename>", methods=['GET'])
@token_required
def serve_static(filename):
    return send_from_directory(globs.p.output_dir, filename)


@app.route("/action", methods=['GET', 'POST'])
@token_required
def action():
    if globs.act == "summarize" and not check_if_run(globs.p):
        msg = "No samples were run yet, there's no point in summarizing"
        current_app.logger.warning(msg)
        flash(msg)
        return redirect(url_for("process"))
    args = argparse.Namespace()
    args_dict = vars(args)
    # Set the arguments from the forms
    for arg in globs.dests:
        value = convert_value(request.form.get(arg))
        args_dict[arg] = value
    # hardcode upfront confirmation in the yes/no query; used in clean and destroy actions
    args_dict["force_yes"] = True
    if globs.log_path is None:
        globs.log_path = os.path.join(globs.p.output_dir, LOG_FILENAME)
    args_dict["logfile"] = globs.log_path
    # perform necessary changes so the looper understands the Namespace
    args_dict = parse_namespace(args_dict)
    # establish the looper log path
    # set the selected computing environment in the Project object
    try:
        globs.p.dcc.activate_package(globs.currently_selected_package)
    except NameError:
        app.logger.info("The compute package was not selected, using 'default'.")
        globs.p.dcc.activate_package("default")
    # run looper action
    run_looper(prj=globs.p, args=args, act=globs.act, log_path=globs.log_path, logging_lvl=globs.logging_lvl)
    get_navbar_summary_links()
    return render_template("/execute.html")


@app.route('/_background_check_status')
def background_check_status():
    app.logger.info("checking flags for {} samples".format(len(list(globs.p.sample_names))))
    flags = get_sample_flags(globs.p, list(globs.p.sample_names))
    if all(not value for value in flags.values()) and not globs.run:
        return jsonify(status_table="No samples were processed yet. " \
                                    "Use <code>looper run</code> and then check the status",
                       interval=globs.poll_interval)
    elif any(value for value in flags.values()):
        return jsonify(status_table=create_status_table(globs.p, final=False) + sample_info_hint(globs.p),
                       interval=globs.poll_interval)
    else:
        return jsonify(status_table=MISSING_SAMPLE_DATA_TXT, interval=globs.poll_interval)


@app.route('/_background_result')
def background_result():
    page = compile_results_content(globs.log_path, globs.act)
    return jsonify(result=textile(page))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'caravel.ico', mimetype='image/vnd.microsoft.icon')


def main():
    ensure_version()
    parser = CaravelParser()
    args = parser.parse_args()
    app.config["port"] = args.port
    app.config["project_configs"] = args.config
    app.config["DEBUG"] = args.debug
    app.config["demo"] = args.demo
    app.config['SECRET_KEY'] = 'thisisthesecretkey'
    app.config['login'] = getpass.getuser()
    globs.init_globals()
    if app.config["DEBUG"]:
        warnings.warn("You have entered the debug mode. The server-client connection is not secure!")
        globs.logging_lvl = logging.DEBUG
    else:
        generate_token(token=parse_token_file())
    app.logger.info("Using python {}".format(python_version()))
    app.run(port=args.port, host='0.0.0.0')


if __name__ == "__main__":
    main()
