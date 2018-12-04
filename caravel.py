import itertools
import glob
import os
import shutil
import sys
import tempfile
import psutil
import yaml
import peppy
from flask import Blueprint, Flask, render_template, redirect, url_for, request, jsonify

app = Flask(__name__)

summary = Blueprint('summary', __name__,
    template_folder='/sfs/lustre/allocations/shefflab/processed/mpfc_neurons/')

CONFIG_ENV_VAR = "CARAVEL"
CONFIG_PRJ_KEY = "projects"


@app.route("/")
def index():
    # helper functions
    def glob_if_exists(x):
        """return all matches in the directory for x and x if nothing matches"""
        return list(itertools.chain(*[
            glob.glob(e) or x for e in (x if isinstance(x, list) else [x])]))

    project_list_path = app.config.get("project_configs") or os.getenv(CONFIG_ENV_VAR)

    if project_list_path is None:
        msg = "Please set the environment variable {} or provide a YAML file " \
              "listing paths to project config files".format(CONFIG_ENV_VAR)
        print(msg)
        return render_template('index.html', warning=msg)

    project_list_path = os.path.expanduser(project_list_path)
    print(project_list_path)

    if not os.path.isfile(project_list_path):
        msg = "Project configs list isn't a file: {}".format(project_list_path)
        print(msg)
        return render_template('index.html', warning=msg)

    with open(project_list_path, 'r') as stream:
        pl = yaml.safe_load(stream)
        assert CONFIG_PRJ_KEY in pl, \
            "'{}' key not in the projects list file.".format(CONFIG_PRJ_KEY)
        projects = pl[CONFIG_PRJ_KEY]
        # get all globs and return unnested list
        projects = [f for prj in projects for f in
                    glob_if_exists(os.path.expanduser(os.path.expandvars(prj)))]

    return render_template('index.html', projects=projects)


@app.route("/process", methods=['GET', 'POST'])
def process():
    # if request.method == 'GET':
    #     return redirect(url_for("index"))
    global p
    global config_file
    global p_info
    global selected_subproject
    selected_project = request.form.get('select_project')
    print(selected_project)
    selected_project = selected_project or p.config_file
    print("\nLoading project: " + selected_project)
    
    config_file = os.path.expandvars(os.path.expanduser(selected_project))
    p = peppy.Project(config_file)

    try:
        subprojects = list(p.subprojects.keys())
    except:
        subprojects = None

    try:
        selected_subproject = request.form.get('subprojects')
        if selected_project is None:
            p = peppy.Project(config_file)
        else:
            p.activate_subproject(selected_subproject)
    except:
        selected_subproject = None

    p_info = {
        "name": p.name,
        "config_file": p.config_file,
        "sample_count": p.num_samples,
        "summary_html": "{project_name}_summary.html".format(project_name=p.name),
        "subprojects": subprojects
    }
    options = {
        "run": ["--ignore-flags","--allow-duplicate-names","--compute","--env","--limit","--lump","--lumpn","--file-checks","--dry-run","--exclude-protocols","--include-protocols","--sp"],
        "check": ["--all-folders","--file-checks","--dry-run","--exclude-protocols","--include-protocols","--sp"],
        "destroy": ["--file-checks","--force-yes","--dry-run","--exclude-protocols","--include-protocols","--sp"],
        "summarize": ["--file-checks","--dry-run","--exclude-protocols","--include-protocols","--sp"]
    }
    psummary = Blueprint(p.name, __name__, template_folder=p.metadata.output_dir)

    @psummary.route("/{pname}/summary/<path:page_name>".format(pname=p.name), methods=['GET'])
    def render_static(page_name):
        return render_template('%s' % page_name)
    try:
        app.register_blueprint(psummary)
    except AssertionError:
        print("this blueprint was already registered")

    return render_template('process.html', p_info=p_info, options=None, sp=selected_subproject)

@app.route('/_background_subproject')
def background_subproject():
	global p
	global config_file
	sp = request.args.get('sp', type=str)
	print(config_file)
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
    options = {
        "run": ["--ignore-flags","--allow-duplicate-names","--compute","--env","--limit","--lump","--lumpn","--file-checks","--dry-run","--exclude-protocols","--include-protocols","--sp"],
        "check": ["--all-folders","--file-checks","--dry-run","--exclude-protocols","--include-protocols","--sp"],
        "destroy": ["--file-checks","--force-yes","--dry-run","--exclude-protocols","--include-protocols","--sp"],
        "summarize": ["--file-checks","--dry-run","--exclude-protocols","--include-protocols","--sp"]
    }
    act = request.args.get('act', type=str)
    options_act = options[act]
    return jsonify(options=render_template('options.html', options=options_act))

@app.route("/execute", methods=['GET', 'POST'])
def action():
    action = request.form['actions']
    opt = list(set(request.form.getlist('opt')))
    print("\nSelected flags:\n " + '\n'.join(opt)) 
    print("\nSelected action: " + action)
    cmd = "looper " + action + " " + ' '.join(opt) + " " + config_file
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
    app.run()
