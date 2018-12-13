from __future__ import print_function
from itertools import chain
import glob
import os
import shutil
import sys
import tempfile
import psutil
import yaml
import peppy
from flask import Blueprint, Flask, render_template, redirect, url_for, request, jsonify, make_response, session
import jwt
import datetime
from functools import wraps
import string
import random
from uuid import uuid1

app = Flask(__name__)

CONFIG_ENV_VAR = "CARAVEL"
CONFIG_PRJ_KEY = "projects"

# Helper functions
def glob_if_exists(x):
    """
    Return all matches in the directory for x and x if nothing matches
    :param x: a string with path containing globs
    :return: a list of paths
    """
    if isinstance(x, list):
        return [glob.glob(e) if len(glob.glob(e)) > 0 else e for e in x]
    else:
        return glob.glob(x) if len(glob.glob(x)) > 0 else [x]

def flatten(x):
    """
    Flatten one level of nesting
    :param x: a list to flatten
    :return: a flat list
    """
    return list(chain.from_iterable(x))

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    global login_uid
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    try:
        login_uid.int
        if login_uid.int == session['uid'].int:
                session.pop('token', None)
                func()
        else:
            msg = "Other instance of Caravel is running elsewhere." \
                  " The session UID in use and your session UID do not match"
            print(msg)
            return render_template('error.html', e=[msg])
    except:
        try:
            del login_uid
        except NameError:
            pass
        session.pop('token', None)
        func()



def token_required(func):
    """
    This decorator checks for a token, verifies if it is valid
    and redirects to the login page if needed
    :param func: function to be decorated
    :return: decorated function
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        global login_uid
        token = request.args.get('token')
        if token is not None:
            try:
                jwt.decode(token, app.config['SECRET_KEY'])
                eprint("Using token from URL argument")
            except:
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
                eprint(token)
            except (NameError, KeyError):
                eprint("No token in session and no argument. Log in")
                return redirect(url_for('login'))
            except:
                return render_template("invalid_token.html"), 403
        return func(*args, **kwargs)
    return decorated


def random_string(n):
    """
    Generates a random string of length N (token), prints a message
    :param n: length of the string to be generated
    :return: random string
    """
    eprint("CSRF token generated")
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(n))


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def geprint(txt):
    """
    Print the provided text to stderr in green. Used to print the token for the user.
    :param txt: string with text to be printed.
    :return: None
    """
    eprint("\033[92m {}\033[00m".format(txt))


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = random_string(10)
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
    session.pop('uid', None)
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
        token = jwt.encode({"payload" : login_uid.int}, app.config['SECRET_KEY'])
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

    psummary = Blueprint(p.name, __name__, template_folder=p.output_dir)

    @psummary.route("/{pname}/summary/<path:page_name>".format(pname=p.name), methods=['GET'])
    def render_static(page_name):
        return render_template('%s' % page_name)

    try:
        app.register_blueprint(psummary)
    except AssertionError:
        print("this blueprint was already registered")

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
    act = request.args.get('act', type=str)
    geprint(act)
    summary_string = "{output_dir}/{summary_html}".format(output_dir=p_info["output_dir"], summary_html=p_info["summary_html"])
    geprint(summary_string)
    return jsonify(summary=render_template('summary.html', summary=summary_string))


@app.route("/action", methods=['GET', 'POST'])
@token_required
def action():
    global act
    opt = list(set(request.form.getlist('opt')))
    print("\nSelected flags:\n " + '\n'.join(opt))
    print("\nSelected action: " + act)
    cmd = "looper " + act + " " + ' '.join(opt) + " " + config_file
    print("\nCreated Command: " + cmd)
    tmpdirname = tempfile.mkdtemp("tmpdir")
    print("\nCreated temporary directory: " + tmpdirname)
    file_run = open(tmpdirname + "/output.txt", "w")
    proc_run = psutil.Popen(cmd, shell=True, stdout=file_run)
    proc_run.wait()
    with open(tmpdirname + "/output.txt", "r") as myfile:
        output_run = myfile.readlines()
    shutil.rmtree(tmpdirname)
    return render_template("execute.html", output=output_run)


if __name__ == "__main__":
    app.config["project_configs"] = sys.argv[1] if len(sys.argv) > 1 else None
    app.config["TOKEN_EXPIRATION"] = int(sys.argv[2]) if len(sys.argv) > 2 else None
    app.config['SECRET_KEY'] = 'thisisthesecretkey'
    app.run()
