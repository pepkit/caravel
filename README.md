[![PEP compatible](http://pepkit.github.io/img/PEP-compatible-green.svg)](http://pepkit.github.io)

# caravel

A local web GUI for [looper](https://looper.readthedocs.io/). Caravel gives you a slick web interface to interact with your projects formatted as [PEPs](http://pepkit.github.io). You can use it to submit jobs to any cluster resource manager, monitor jobs, summarize results, and browse project summary web pages. `caravel` basically builds on top of `looper`, but uses the lightweight `flask` microframework to give you a web interface, making it even easier to manage your jobs for those who like pointy-clicky.


# Run a web-server


Run like:

```
FLASK_APP=caravel.py flask run
```

Then point browser to: http://127.0.0.1:5000



Debug mode is: 

```
FLASK_APP=caravel.py FLASK_ENV=development flask run
```

# Run on a remote server (like a head node for a compute cluster):

Caravel runs a very basic web server that lets you interact with it through the browser. What if you want to use a local browser, but connect to data and `looper` processing that lives on a remote server? You can use an `SSH` tunnel to map a local port to the remote port. It's quite simple, actually. When you `ssh` into the server, you use the `-L` flag to map the port like this:

```
ssh -L 5000:localhost:5000 user@server
```

Since `flask` (and `caravel`) uses port 5000 by default, this maps your localhost port 5000 to the server port 5000. You can now access the `caravel` GUI using your local web browser, pointing at: `http://localhost:5000`.

So a complete one-line command to run `caravel` remotely with a local web GUI would be something like this:

```
ssh -L 5000:localhost:5000 user@server "FLASK_APP=${REMOTE_CODEBASE}/caravel/caravel.py flask run"
```

# How it works

* Set environment variable `$CARAVEL` to point to a YAML file formatted as shown below:

```
projects:
  - path/to/project1_config.yaml
  - path/to/project2_config.yaml
```

* The application will read the file and let you select the project of interest from a dropdown list

* [`peppy`](https://peppy.readthedocs.io/en/latest/index.html) will read the *PEP* and the application will display the *PEP* info

* You will have an option to activate a subproject, if available

* Depending on your choice [`looper`](https://looper.readthedocs.io/en/latest/) will `run`/`check`/`destroy` the pipeline specified in the seleted project

* The output produced by `looper` will be displayed

* ...

# The vision

`caravel` will start a server that lets you load up your PEPs and manage them in a centralized web interface. it lets to run jobs, displays results.

