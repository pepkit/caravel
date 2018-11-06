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

# Running it

Drag and drop your PEP (`project_config.yaml` + `sample_annotation.tsv`) files into the "Choose Files" prompt and hit "Go". This will load your project into python using `peppy` and render a result.



# The vision

`caravel` will start a server that lets you load up your PEPs and manage them in a centralized web interface. it lets to run jobs, displays results.

