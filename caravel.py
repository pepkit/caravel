from argparse import ArgumentParser
import glob
import os
import peppy
import shutil
import tempfile
import yaml

from flask import Flask, render_template, redirect, url_for, request
app = Flask(__name__)

@app.route("/")
def index():
    try:  
        project_list_path = os.path.expanduser(os.environ["CARAVEL"]); print(project_list_path)
        assert os.path.isfile(project_list_path), "The $CARAVEL environment variable does not point to a file" 
        with open(project_list_path, 'r') as stream:
            pl = yaml.safe_load(stream)
            print(pl)
            assert "projects" in pl, "'projects' key not in the projects list file."
            projects=pl["projects"]
    except KeyError: 
        print "Please set the environment variable $CARAVEL"
        sys.exit(1)

    return(render_template('index.html', projects=projects))

@app.route("/process" , methods=['GET', 'POST'])
def process():
    print("in Process")
    selected_project = request.form.get('select_project')
    print("Loading project: " + selected_project)
    p = peppy.Project(selected_project)
    # print(p)
    return(render_template('process.html', p=p))
   
