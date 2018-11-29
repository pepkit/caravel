import glob
import os
import peppy
import psutil
import shutil
import tempfile
import yaml


from flask import Blueprint, Flask, render_template, redirect, url_for, request
app = Flask(__name__)

summary = Blueprint('summary', __name__,
                        template_folder='/sfs/lustre/allocations/shefflab/processed/mpfc_neurons/')


@app.route("/")
def index():
    
    # helper functions
    def glob_if_exists(x):
        """return all matches in the directory for x and x if nothing matches"""
        if isinstance(x, list):
            return [glob.glob(e) if len(glob.glob(e)) > 0 else e for e in x]
        else:
            return glob.glob(x) if len(glob.glob(x)) > 0 else x

    try:  
        project_list_path = os.path.expanduser(
            os.environ["CARAVEL"])
        print(project_list_path)
        if not os.path.isfile(project_list_path):
            msg = "The $CARAVEL environment variable does not point to a file"
            print(msg)
            return(render_template('index.html', warning=msg))
        
        with open(project_list_path, 'r') as stream:
            pl = yaml.safe_load(stream)
            assert "projects" in pl, "'projects' key not in the projects list file."
            projects = pl["projects"]
            # expand user and environment variables
            projects = [os.path.expanduser(os.path.expandvars(x)) for x in projects]
            # get all globs and return unnested list
            glob_projects = []
            for x in projects:
                glob_element = glob_if_exists(x)
                if isinstance(glob_element, list):
                    glob_projects.extend(glob_element)
                else:
                    glob_projects.append(x)
            projects = glob_projects

    except KeyError: 
        msg = "Please set the environment variable $CARAVEL"
        print(msg)
        return(render_template('index.html', warning=msg))

    return(render_template('index.html', projects=projects))

@app.route("/process", methods=['GET', 'POST'])
def process():
    # if request.method == 'GET':
    #     return redirect(url_for("index"))
    global p
    global config_file
    global p_info
    selected_project = request.form.get('select_project')
    print(selected_project)
    if selected_project is None:
        selected_project = p.config_file
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
    psummary = Blueprint(p.name, __name__,
        template_folder=p.metadata.output_dir)

    @psummary.route("/{pname}/summary/<path:page_name>".format(pname=p.name), methods=['GET'])
    def render_static(page_name):
        return render_template('%s' % page_name)
    try:
        app.register_blueprint(psummary)
    except AssertionError:
        print("this blueprint was already registered")

    return(render_template('process.html', p_info=p_info, options=options, sp=selected_subproject))

@app.route("/execute", methods=['GET','POST'])
def action():
    action = request.form['actions']
    opt = list(set(request.form.getlist('opt')))
    print("\nSelected flags:\n " + '\n'.join(opt)) 
    print("\nSelected action: " + action)
    cmd = "looper " + action + " " + ' '.join(opt) + " " + config_file
    print("\nCreated Command: " + cmd)
    tmpdirname = tempfile.mkdtemp("tmpdir")
    print("\nCreated temporary directory: " + tmpdirname)
    file_run = open(tmpdirname + "/output.txt","w")
    proc_run = psutil.Popen(cmd, shell=True, stdout=file_run)
    proc_run.wait()
    with open (tmpdirname + "/output.txt", "r") as myfile:
        output_run=myfile.readlines()
    shutil.rmtree(tmpdirname)
    return(render_template("execute.html", output=output_run))

