from argparse import ArgumentParser
import glob
import os
import peppy
import psutil
import shutil
import sys
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
            return [glob.glob(e) if len(glob.glob(e))>0 else e for e in x]
        else:
            return glob.glob(x) if len(glob.glob(x))>0 else x

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
                if isinstance(glob_element,list):
                    glob_projects += glob_element
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
    selected_project = request.form.get('select_project')
    print("\nLoading project: " + selected_project)
    global config_file
    config_file = os.path.expandvars(os.path.expanduser(selected_project))
    p = peppy.Project(config_file)
    p_info = {
        "name": p.name,
        "config_file": p.config_file,
        "sample_count": len(p.samples),
        "summary_html": "{project_name}_summary.html".format(project_name=p.name)
    }

    p.metadata.output_dir

    psummary = Blueprint(p.name, __name__,
        template_folder=p.metadata.output_dir)

    @psummary.route("/{pname}/summary/<path:page_name>".format(pname=p.name),methods=['GET'])
    def render_static(page_name):
        return render_template('%s' % page_name)
    try:
        app.register_blueprint(psummary)
    except AssertionError:
        print("this blueprint was already registered")

    return(render_template('process.html', p_info=p_info))


@app.route("/execute/run", methods=['GET','POST'])
def run():
    # if request.method == 'POST':
    options = request.form['opts']
    print("\nAppending options: " + options + "\n")
    cmd = "looper run " + options + " " + config_file
    print("\ncommand: " + cmd)
    tmpdirname = tempfile.mkdtemp("tmpdir")
    print("\nCreated temporary directory: " + tmpdirname)
    file_run = open(tmpdirname + "/output_run.txt","w")
    proc_run = psutil.Popen(cmd, shell=True,stdout=file_run)
    proc_run.wait()
    with open (tmpdirname + "/output_run.txt", "r") as myfile:
        output_run=myfile.readlines()
    shutil.rmtree(tmpdirname)
    return(render_template("execute.html",output=output_run))


@app.route("/execute/check", methods=['GET','POST'])
def check():
    cmd = "looper check " + config_file
    tmpdirname = tempfile.mkdtemp("tmpdir")
    print("\n\nCreated temporary directory: " + tmpdirname)
    file_check = open(tmpdirname + "/output_check.txt","w")
    proc_check = psutil.Popen(cmd, shell=True,stdout=file_check)
    proc_check.wait()
    with open (tmpdirname + "/output_check.txt", "r") as myfile:
        output_check=myfile.readlines()
    shutil.rmtree(tmpdirname)
    return(render_template("execute.html",output=output_check))


@app.route("/execute/destroy", methods=['GET','POST'])
def destroy():
    cmd = "looper destroy " + config_file
    tmpdirname = tempfile.mkdtemp("tmpdir")
    print("\n\nCreated temporary directory: " + tmpdirname)
    file_destroy = open(tmpdirname + "/output_destroy.txt","w")
    proc_destroy = psutil.Popen(cmd, shell=True,stdout=file_destroy)
    proc_destroy.wait()
    with open (tmpdirname + "/output_destroy.txt", "r") as myfile:
        output_destroy=myfile.readlines()
    shutil.rmtree(tmpdirname)
    return(render_template("execute.html",output=output_destroy))

