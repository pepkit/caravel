# caravel

A local web GUI for `looper`.


# Run a web-server

`caravel` uses the lightweight `flask` microframework to give you a web interface, making it even easier if you like pointy-clicky.

Run like:

```
FLASK_APP=caravel.py flask run
```

Then point browser to: http://127.0.0.1:5000



Debug mode is: 

```
FLASK_APP=caravel.py FLASK_ENV=development flask run
```

# How it works

* Set enviroment variable `$CARAVEL` to point to a YAML file formatted as shown below:

```
projects:
  - path/to/project1_config.yaml
  - path/to/project2_config.yaml
```

* The application will read the file and let you select the project of interest from a dropdown list

* [`peppy`](https://peppy.readthedocs.io/en/latest/index.html) will read the *PEP* and the application will display the *PEP* info

* Depending on your choice [`looper`](https://looper.readthedocs.io/en/latest/) will `run`/`check`/`destroy` the pipeline specified in the seleted project

* The output produced by `looper` will be displayed

* ...

# The vision

`caravel` will start a server that lets you load up your PEPs and manage them in a centralized web interface. it lets to run jobs, displays results.

