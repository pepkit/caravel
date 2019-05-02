[logo]: img/logo_caravel.svg

# ![logo][logo] Caravel


[![PEP compatible](http://pepkit.github.io/img/PEP-compatible-green.svg)](http://pepkit.github.io)

`Caravel` provides a web interface to interact with your [PEP-formatted projects](http://pepkit.github.io). `Caravel` lets you submit jobs to any cluster resource manager, monitor jobs, summarize results, and browse project summary web pages. `Caravel` is a local web GUI for [looper](https://code.databio.org/looper/) build with [flask](http://flask.pocoo.org/).

## Installing

Release versions are posted on the GitHub [caravel releases page](https://github.com/databio/caravel/releases). You can install the latest release directly from GitHub using `pip`:

```bash
pip install --user https://github.com/pepkit/caravel/zipball/master
```

Update `caravel` with:

```bash
pip install --user --upgrade https://github.com/pepkit/caravel/zipball/master
```
## Hello, world!

You can now try running it 

```bash
caravel -c example_caravel.yaml
```

## Setup and configuration

* Set environment variable `$CARAVEL` to point to a [YAML file](http://yaml.org) with a hypen-bulleted list of [PEP config files](https://pepkit.github.io/docs/project_config/), like this:

```yaml
projects:
  - path/to/project1_config.yaml
  - path/to/project2_config.yaml
```

## Run a web server

From within the root of the cloned repository

**Run like**:

```bash
caravel -c example_config.yaml
```

The `example_config.yaml` file is a simple configuration file that points to your PEPs. See [how to configure caravel](configure-caravel).

Both `looper` and `caravel` logging levels can be changed by toggling the debug mode at the server launch (`-d`, `--dbg` options). 
By default all the errors, warnings and information are displayed. The debug logs are activated when in debug mode.
