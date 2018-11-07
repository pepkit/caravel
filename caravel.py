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
    
    # Browsers aren't allowed to access the actual files stuck into HTML boxes for security reasons,
    # so we have to actually copy those into a temporary location and read them from there.
    # I couldn't figure out how to use the actual files; I don't think it's possible (even with javascript)
    # because of intended security limitation of browsers that prevents them from seeing the actual file system.

    uploaded_files = request.files.getlist("pconfig")
    print(uploaded_files)

    tmpdirname = tempfile.mkdtemp("tmpdir")
    print('Created temporary directory:', tmpdirname)

    pconfig = ""
    # We have to upload multiple files (the config plus sample annotation);
    # here we have to figure out which one ends in `yaml` -- that's the config
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

    # Now I delete the temporary PEP components; but this could be done later
    
    shutil.rmtree(tmpdirname)
    return(retval)
   
