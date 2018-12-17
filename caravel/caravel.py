from functools import wraps
import os
import shutil
import tempfile
from uuid import uuid1

from flask import Blueprint, Flask, render_template, redirect, url_for, request, jsonify, session
import jwt
import psutil
import peppy
import yaml
from .helpers import *

app = Flask(__name__)

CONFIG_ENV_VAR = "CARAVEL"
CONFIG_PRJ_KEY = "projects"


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
            eprint("{k} not found in the session".format(k=key))


def shutdown_server():
    shut_func = request.environ.get('werkzeug.server.shutdown')
    global login_uid
    if shut_func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    if login_uid.int == session['uid'].int:
            clear_session_data(keys=['token', '_csrf_token', 'uid'])
            shut_func()
    else:
        msg = "Other instance of Caravel is running elsewhere." \
              " The session UID in use and your session UID do not match"
        print(msg)
        return render_template('error.html', e=[msg])


def token_required(func):
    """
    This decorator checks for a token, verifies if it is valid
    and redirects to the login page if needed
    :param callable func: function to be decorated
    :return callable: decorated function
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        global login_uid
        token = request.args.get('token')
        if token is not None:
            try:
                jwt.decode(token, app.config['SECRET_KEY'])
                eprint("Using token from URL argument")
            except jwt.exceptions.InvalidTokenError:
                return render_template("invalid_token.html"), 403
        else:
            try:
                session['uid']
                if login_uid.int == session['uid'].int:
                    pass
                else:
                    msg = "Other instance of Caravel is running elsewhere." \
                          " The session UID in use and your session UID do not match"
                    print(msg)
                    return render_template('error.html', e=[msg])
                token = session['token']
                jwt.decode(token, app.config['SECRET_KEY'])
                eprint("Token retrieved from the session")
            except (NameError, KeyError):
                eprint("No token in session and no argument. Log in")
                return redirect(url_for('login'))
            except jwt.exceptions.InvalidTokenError:
                return render_template("invalid_token.html"), 403
        return func(*args, **kwargs)
    return decorated


def generate_csrf_token(n=100):
    """
    Generate a CSRF token
    :param n: length of a token
    :return: flask.session with "_csrf_token_key"
    """
    if '_csrf_token' not in session:
        session['_csrf_token'] = random_string(n)
    else: 
        eprint("CSRF token retrieved from the session")
    return session['_csrf_token']


app.jinja_env.globals['csrf_token'] = generate_csrf_token


# Routes
@app.errorhandler(Exception)
def unhandled_exception(e):
    app.logger.error('Unhandled Exception: %s', (e))
    return render_template('error.html', e=e), 500


@app.route('/shutdown', methods=['GET'])
@token_required
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


@app.route("/login")
def login():
    global login_uid
    # verbosity for testing purposes
    try:
        eprint("Retrieved session UID: " + str(session['uid']))
    except KeyError:
        session['uid'] = uuid1()
        eprint("Generated session UID: " + str(session['uid']))
    try:
        eprint("Using existing login UID: " + str(login_uid))
    except NameError:
        login_uid = session['uid']
        eprint("Assigned new login UID: " + str(login_uid))

    if login_uid.int == session['uid'].int:
        token = jwt.encode({"payload": login_uid.int}, app.config['SECRET_KEY'])
        session['token'] = token
        eprint("\n\nCaravel is protected with a token.\nCopy this link to your browser to authenticate:\n")
        geprint("http://localhost:5000/?token=" + token.decode('UTF-8').strip() + "\n")
    else:
        msg = "Other instance of Caravel is running elsewhere." \
              " The session UID in use and your session UID do not match"
        print(msg)
        return render_template('error.html', e=[msg])
    return render_template('token.html')


@app.before_request
def csrf_protect():
    if request.method == "POST":
        global login_uid
        try:
            login_uid.int
        except NameError:
            login_uid = session['uid']
        if login_uid.int == session['uid'].int:
            token_csrf = session['_csrf_token']
            token_get_csrf = request.form.get("_csrf_token")
            if not token_csrf or token_csrf != token_get_csrf:
                msg = "The CSRF token is invalid"
                print(msg)
                return render_template('error.html', e=[msg])
        else:
            msg = "Other instance of Caravel is running elsewhere." \
                  " The session UID in use and your session UID do not match"
            print(msg)
            return render_template('error.html', e=[msg])


@app.route("/")
@token_required
def index():

    project_list_path = app.config.get("project_configs") or os.getenv(CONFIG_ENV_VAR)

    if project_list_path is None:
        msg = "Please set the environment variable {} or provide a YAML file " \
              "listing paths to project config files".format(CONFIG_ENV_VAR)
        print(msg)
        return render_template('error.html', e=[msg])

    project_list_path = os.path.expanduser(project_list_path)

    if not os.path.isfile(project_list_path):
        msg = "Project configs list isn't a file: {}".format(project_list_path)
        print(msg)
        return render_template('error.html', e=[msg])

    with open(project_list_path, 'r') as stream:
        pl = yaml.safe_load(stream)
        assert CONFIG_PRJ_KEY in pl, \
            "'{}' key not in the projects list file.".format(CONFIG_PRJ_KEY)
        projects = pl[CONFIG_PRJ_KEY]
        # get all globs and return unnested list
        projects = flatten([glob_if_exists(os.path.expanduser(os.path.expandvars(prj))) for prj in projects])

    return render_template('index.html', projects=projects)


@app.route("/process", methods=['GET', 'POST'])
@token_required
def process():
    global p
    global config_file
    global p_info
    global selected_subproject
    selected_project = request.form.get('select_project')

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
            p.activate_subproject(selected_subproject)
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

    return render_template('process.html', p_info=p_info)


@app.route('/_background_subproject')
def background_subproject():
    global p
    global config_file
    sp = request.args.get('sp', type=str)
    if sp == "reset":
        output = "No subproject activated"
        p = peppy.Project(config_file)
        sps = p.num_samples
    else:
        output = "Activated suproject: " + sp
        p.activate_subproject(sp)
        sps = p.num_samples
    return jsonify(subproj_txt=output, sample_count=sps)


@app.route('/_background_options')
def background_options():
    global p_info
    global selected_subproject
    global act
    # TODO: the options have to be retrieved from the looper argument parser
    # argparse.ArgumentParser._actions has all the info needed to determine what kind (or absence) of input is needed
    options = {
        "run": ["--ignore-flags", "--allow-duplicate-names", "--compute", "--env", "--limit", "--lump", "--lumpn",
                "--file-checks", "--dry-run", "--exclude-protocols", "--include-protocols", "--sp"],
        "check": ["--all-folders", "--file-checks", "--dry-run", "--exclude-protocols", "--include-protocols", "--sp"],
        "destroy": ["--file-checks", "--force-yes", "--dry-run", "--exclude-protocols", "--include-protocols", "--sp"],
        "summarize": ["--file-checks", "--dry-run", "--exclude-protocols", "--include-protocols", "--sp"]
    }
    act = request.args.get('act', type=str)
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
    # To be changed in future version. Looper will be imported and run within Caravel
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
    app.config["project_configs"] = sys.argv[1] if len(sys.argv) > 1 else None
    app.config['SECRET_KEY'] = 'thisisthesecretkey'
    app.run()
