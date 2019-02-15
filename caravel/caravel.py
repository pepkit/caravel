""" Main UI application for using looper """

from functools import wraps
import logging
import traceback
import warnings
from flask import Blueprint, Flask, render_template, request, jsonify, session, redirect, send_from_directory
import yaml
from _version import __version__ as caravel_version
from const import *
from helpers import *
from looper_parser import *
import divvy
import peppy
import textile
from peppy.utils import coll_like
from platform import python_version


logging.getLogger().setLevel(logging.INFO)

app = Flask(__name__)
app.logger.info("Using python {}".format(python_version()))

@app.context_processor
def inject_dict_for_all_templates():
    return dict(caravel_version=caravel_version, looper_version=LOOPER_VERSION, referrer=request.referrer)


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
    :return: flask.render_template
    """
    global login_token
    login_token = token or random_string(n)
    eprint("\nCaravel is protected with a token.\nCopy this link to your browser to authenticate:\n")
    geprint("http://localhost:5000/?token=" + login_token + "\n")


def token_required(func):
    """
    This decorator checks for a token, verifies if it is valid
    and redirects to the login page if needed
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
    :return: flask.session with "_csrf_token_key"
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
    return render_template('error.html', e=e, types=[e.__class__.__name__]), 500


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

    :return list[str] project list
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
        assert token_unique_len >= 5, "The predefined authentication token in the config file has to be composed " \
            "of at least 5 unique characters, got {len} in '{token}'.".format(len=token_unique_len, token=token)
        app.logger.info("{} file found, using the predefined token".format(TOKEN_FILE_NAME))
    except IOError:
        token = None
    return token


# Routes
@app.route("/")
@token_required
def index():
    global projects
    projects = parse_config_file()
    return render_template('index.html', projects=projects)


@app.route("/set_comp_env")
@token_required
def set_comp_env():
    global compute_config
    global selected_package
    global compute_packages
    global active_settings
    global user_selected_package
    global env_file_path

    try:
        compute_config
    except NameError:
        env_file_path = os.getenv(COMPUTE_SETTINGS_VARNAME)
        if env_file_path is not None:
            app.logger.info("Found the `{}` environment variable".format(COMPUTE_SETTINGS_VARNAME))
            if not os.path.isfile(env_file_path):
                raise ValueError("'{var_name}' environment variable points to '{file}', which does not exist"
                                 .format(var_name=COMPUTE_SETTINGS_VARNAME, file=env_file_path))
            app.logger.info("File `{}` exists".format(env_file_path))
            compute_config = divvy.ComputingConfiguration(env_file_path)
            compute_packages = compute_config.list_compute_packages()
        else:
            app.logger.info("Didn't find the '{}' environment variable".format(COMPUTE_SETTINGS_VARNAME))
            return render_template('set_comp_env.html', compute_packages=None, env_var_name=COMPUTE_SETTINGS_VARNAME)
    selected_package = request.args.get('compute', type=str)
    try:
        user_selected_package
    except NameError:
        user_selected_package = "default"
    if selected_package is not None:
        success = compute_config.clean_start(selected_package)
        if not success:
            msg = "Compute package '{}' cannot be activated".format(selected_package)
            app.logger.warning(msg)
            return jsonify(active_settings=render_template('compute_info.html', active_settings=None, msg=msg))
        user_selected_package = selected_package
        active_settings = compute_config.get_active_package()
        return jsonify(active_settings=render_template('compute_info.html', active_settings=active_settings))
    active_settings = compute_config.get_active_package()
    return render_template('set_comp_env.html', env_conf_file=env_file_path, compute_packages=compute_packages,
                           active_settings=active_settings, user_selected_package=user_selected_package)


@app.route("/process", methods=['GET', 'POST'])
@token_required
def process():
    global p
    global config_file
    global p_info
    global selected_subproject
    global selected_project
    global projects

    # this try-except block is used to determine whether the user should be redirected to the index page
    # to select the project when they land on the process subpage from the set_comp_env subpage
    try:
        selected_project
    except NameError:
        selected_project = request.form.get('select_project')
        if selected_project is None:
            app.logger.info("The project is not selected, redirecting to the index page.")
            return render_template('index.html', projects=projects)
    else:
        new_selected_project = request.form.get('select_project')
        if new_selected_project is not None and selected_project != new_selected_project:
            selected_project = new_selected_project

    config_file = os.path.expandvars(os.path.expanduser(selected_project))
    p = peppy.Project(config_file)

    try:
        subprojects = list(p.subprojects.keys())
    except AttributeError:
        subprojects = None

    try:
        selected_subproject = request.form['subprojects']
        if selected_project is None:
            p = peppy.Project(config_file)
        else:
            try:
                p.activate_subproject(selected_subproject)
            except AttributeError:
                return render_error_msg("Your peppy version does not implement the subproject activation "
                                        "functionality. Consider upgrading it to version >= 0.19. "
                                        "See: https://github.com/pepkit/peppy/releases")
    except KeyError:
        selected_subproject = None

    p_info = {
        "name": p.name,
        "config_file": p.config_file,
        "sample_count": p.num_samples,
        "summary_html": "{project_name}_summary.html".format(project_name=p.name),
        "output_dir": p.metadata.output_dir,
        "subprojects": subprojects
    }

    return render_template('process.html', p_info=p_info, change=None)


@app.route('/_background_subproject')
def background_subproject():
    global p
    global config_file
    sp = request.args.get('sp', type=str)
    if sp == "reset":
        output = "No subproject activated"
        p = peppy.Project(config_file)
    else:
        try:
            p.activate_subproject(sp)
            output = "Activated suproject: " + sp
        except AttributeError:
            output = "Upgrade peppy, see terminal for details"
            app.logger.warning("Your peppy version does not implement the subproject activation functionality. "
                             "Consider upgrading it to version >= 0.19. See: https://github.com/pepkit/peppy/releases")
    return jsonify(subproj_txt=output, sample_count=p.num_samples)


@app.route('/_background_options')
def background_options():
    global p_info
    global selected_subproject
    global act
    global dests
    from looper.looper import build_parser as blp
    act = request.args.get('act', type=str) or "run"
    parser_looper = blp()
    html_elements_info = get_html_elements_info(parser_looper, act)
    dests = html_elements_info[2]
    return jsonify(options=render_template('options.html', html_elements_info=html_elements_info))


@app.route('/_background_summary_notice')
def background_summary_notice():
    global p_info
    global summary_string
    global summary_location
    summary_location = "{output_dir}/{summary_html}".format(output_dir=p_info["output_dir"],
                                                            summary_html=p_info["summary_html"])
    if os.path.isfile(summary_location):
        psummary = Blueprint(p.name, __name__, template_folder=p_info["output_dir"])

        @psummary.route("/{pname}/summary/<path:page_name>".format(pname=p_info["name"]), methods=['GET'])
        def render_static(page_name):
            return render_template('%s' % page_name)
        try:
            app.register_blueprint(psummary)
        except AssertionError:
            app.logger.info("this blueprint was already registered")
        summary_string = "{name}/summary/{summary_html}".format(name=p_info["name"],
                                                                summary_html=p_info["summary_html"])
        return jsonify(present="1")
    else:
        return jsonify(present="0", summary=render_template('summary_notice.html'))


@app.route('/summary', methods=['POST'])
def summary():
    global summary_string
    return redirect(summary_string)


@app.route("/action", methods=['GET', 'POST'])
@token_required
def action():
    global act
    global p
    global selected_subproject
    global dests
    global user_selected_package
    global env_file_path
    global log_path
    args = argparse.Namespace()
    args_dict = vars(args)
    # Set the arguments from the forms
    for arg in dests:
        value = convert_value(request.form.get(arg))
        args_dict[arg] = value
    # Set the previously selected arguments: config_file, subproject, computing environment
    args_dict["config_file"] = str(p.config_file)
    args_dict["subproject"] = selected_subproject
    try:
        args_dict["compute"] = user_selected_package
        args_dict["env"] = env_file_path
    except NameError:
        app.logger.info("The compute package was not selected, using 'default'.")
        args_dict["compute"] = "default"
    # perform necessary changes so the looper understands the Namespace
    args_dict = parse_namespace(args_dict)
    # establish the looper log path
    log_path = os.path.join(p_info["output_dir"], LOG_FILENAME)
    # run looper
    run_looper(args=args, act=act, log_path=log_path)
    return render_template("execute.html")


@app.route('/_background_result')
def background_result():
    global p_info
    global log_path
    with open(log_path, "r") as log:
        log_content = log.read()
    return jsonify(result=textile.textile(log_content))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'caravel.ico', mimetype='image/vnd.microsoft.icon')


def main():
    ensure_looper_version()
    parser = CaravelParser()
    args = parser.parse_args()
    app.config["project_configs"] = args.config
    app.config["DEBUG"] = args.debug
    app.config['SECRET_KEY'] = 'thisisthesecretkey'
    if app.config["DEBUG"]:
        warnings.warn("You have entered the debug mode. The server-client connection is not secure!")
    else:
        generate_token(token=parse_token_file())
    app.run()


if __name__ == "__main__":
    main()
