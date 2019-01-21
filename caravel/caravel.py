""" Main UI application for using looper """

from functools import wraps
import shutil
import tempfile
from flask import Blueprint, Flask, render_template, request, jsonify, session
import psutil
import peppy
import yaml
import warnings
import traceback
from helpers import *
from _version import __version__ as caravel_version
from looper import __version__ as looper_version
from peppy.utils import coll_like
import logging
from const import *
import looper
import divvy
logging.getLogger().setLevel(logging.INFO)
app = Flask(__name__)


@app.context_processor
def inject_dict_for_all_templates():
    return dict(caravel_version=caravel_version, looper_version=looper_version)


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


def generate_token(config_token=None, n=TOKEN_LEN):
    """
    Set the global app variable login_token to the generated random string of length n.
    If config_token provided, use its value.
    Print info to the terminal
    :param config_token: the token to use
    :param n: length of the token to generate
    :return: flask.render_template
    """
    global login_token
    login_token = random_string(n) if config_token is None else config_token
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
    return render_template('error.html', e=e), 500


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

    :param list[str] sections: list of string names indicating the sections(s) of config file to retrieve.
        Options: "projects", "token" or both
    :return list[str], str: tuple of project list and string with the token.
        If neither is requested, None is returned instead
    """

    project_list_path = app.config.get("project_configs") or os.getenv(CONFIG_ENV_VAR)
    if project_list_path is None:
        raise ValueError("Please set the environment variable {} or provide a YAML file listing paths to project "
                         "config files".format(CONFIG_ENV_VAR))
    project_list_path = os.path.expanduser(project_list_path)

    if not os.path.isfile(project_list_path):
        raise ValueError("Project configs list isn't a file: {}".format(project_list_path))

    with open(project_list_path, 'r') as stream:
        pl = yaml.safe_load(stream)
        assert CONFIG_PRJ_KEY in pl, \
            "'{}' key not in the projects list file.".format(CONFIG_PRJ_KEY)
        projects = pl[CONFIG_PRJ_KEY]
        projects = sorted(flatten([glob_if_exists(os.path.expanduser(os.path.expandvars(prj))) for prj in projects]))
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
    compute_packages = None
    env_file_path = os.getenv(COMPUTE_SETTINGS_VARNAME)
    if env_file_path is not None:
        app.logger.info("Found the `{}` environment variable".format(COMPUTE_SETTINGS_VARNAME))
        if not os.path.isfile(env_file_path):
            raise ValueError("'{var_name}' environment variable points to '{file}', which does not exist"
                             .format(var_name=COMPUTE_SETTINGS_VARNAME, file=env_file_path))
        app.logger.info("File `{}` exists".format(env_file_path))
        compute_config = divvy.ComputingConfiguration(env_file_path)
        compute_packages = compute_config["compute_packages"].keys()
    else:
        app.logger.info("Didn't find the '{}' environment variable".format(COMPUTE_SETTINGS_VARNAME))
        return render_template('set_comp_env.html', compute_packages=None, env_var_name=COMPUTE_SETTINGS_VARNAME, referrer=request.referrer)
    return render_template('set_comp_env.html', compute_packages=compute_packages)


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
                                        "functionality. Consider upgrading it to version > 0.18.2. "
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
            output="Upgrade peppy, see terminal for details"
            app.logger.warning("Your peppy version does not implement the subproject activation functionality. "
                             "Consider upgrading it to version > 0.18.2. See: https://github.com/pepkit/peppy/releases")
    return jsonify(subproj_txt=output, sample_count=p.num_samples)


@app.route('/_background_options')
def background_options():
    global p_info
    global selected_subproject
    global act
    from looper_parser import get_long_optnames
    from looper.looper import build_parser as blp
    options = get_long_optnames(blp())
    act = request.args.get('act', type=str) or "run"
    options_act = options[act]
    return jsonify(options=render_template('options.html', options=options_act))


@app.route('/_background_summary')
def background_summary():
    global p_info
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
            eprint("this blueprint was already registered")
        summary_string = "{name}/summary/{summary_html}".format(name=p_info["name"],
                                                                summary_html=p_info["summary_html"])
    else:
        summary_string = "Summary not available"
    return jsonify(summary=render_template('summary.html', summary=summary_string, file_name=p_info["summary_html"]))


@app.route("/action", methods=['GET', 'POST'])
@token_required
def action():
    global act
    # To be changed in future version. Looper will be imported and run within caravel
    opt = list(set(request.form.getlist('opt')))
    eprint("\nSelected flags:\n " + '\n'.join(opt))
    eprint("\nSelected action: " + act)
    cmd = "looper " + act + " " + ' '.join(opt) + " " + config_file
    eprint("\nCreated Command: " + cmd)
    tmpdirname = tempfile.mkdtemp("tmpdir")
    eprint("\nCreated temporary directory: " + tmpdirname)
    file_run = open(tmpdirname + "/output.txt", "w")
    proc_run = psutil.Popen(cmd, shell=True, stdout=file_run)
    proc_run.wait()
    with open(tmpdirname + "/output.txt", "r") as myfile:
        output_run = myfile.readlines()
    shutil.rmtree(tmpdirname)
    return render_template("execute.html", output=output_run)


if __name__ == "__main__":
    parser = CaravelParser()
    args = parser.parse_args()
    app.config["project_configs"] = args.config
    app.config["DEBUG"] = args.debug
    app.config['SECRET_KEY'] = 'thisisthesecretkey'
    config_token = parse_token_file()
    if not app.config["DEBUG"]:
        generate_token(config_token=config_token)
    else:
        warnings.warn("You have entered the debug mode. The server-client connection is not secure!")

    app.run()
