from argparse import ArgumentParser
import glob
import os
import peppy
import psutil
import shutil
import sys
import tempfile
import yaml


from flask import Flask, render_template, redirect, url_for, request
app = Flask(__name__)

@app.route("/")
def index():
    try:  
        project_list_path = os.path.expanduser(
            os.environ["CARAVEL"])
        print(project_list_path)
        msg = "The $CARAVEL environment variable does not point to a file" 
        assert os.path.isfile(project_list_path), msg
        return(render_template('index.html', warning=msg))
        with open(project_list_path, 'r') as stream:
            pl = yaml.safe_load(stream)
            print(pl)
            assert "projects" in pl, "'projects' key not in the projects list file."
            projects=pl["projects"]
    except KeyError: 
        msg = "Please set the environment variable $CARAVEL"
        print(msg)
        return(render_template('index.html', warning=msg))

    return(render_template('index.html', projects=projects))

@app.route("/process" , methods=['GET', 'POST'])
def process():
    selected_project = request.form.get('select_project')
    print("\n\nLoading project: " + selected_project)
    global config_file
    config_file = os.path.expandvars(os.path.expanduser(selected_project))
    p = peppy.Project(config_file)
    return(render_template('process.html', p=p))
    
@app.route("/run",methods=['GET','POST'])
def run():
    cmd = "looper run " + config_file
    tmpdirname = tempfile.mkdtemp("tmpdir")
    print("\n\nCreated temporary directory: " + tmpdirname)
    file = open(tmpdirname + "/output.txt","w")
    proc = psutil.Popen(cmd, shell=True,stdout=file)
    proc.wait()
    with open (tmpdirname + "/output.txt", "r") as myfile:
        output=myfile.readlines()
    shutil.rmtree(tmpdirname)
    return(render_template("run.html",output=output))