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
    return render_template('select.html', route="process")


@app.route("/process" , methods=['GET', 'POST'])
def process():

    uploaded_files = request.files.getlist("pconfig")
    print uploaded_files

    tmpdirname = tempfile.mkdtemp("tmpdir")
    print('Created temporary directory:', tmpdirname)

    pconfig = ""
    for f in uploaded_files:
        fullname = "/".join([tmpdirname, f.filename])
        print(fullname)
        fn, file_extension = os.path.splitext(f.filename)
        print(file_extension)
        if file_extension == ".yaml":
            pconfig = fullname
        f.save(fullname)

    print("Config file saved to: " + pconfig)
    
    retval=""
    try:
        p = peppy.Project(pconfig)
        retval = str(p)
        print(p)
    except:
        pass


    shutil.rmtree(tmpdirname)
    return(retval)
   