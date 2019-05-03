[logo]: img/logo_caravel.svg

# ![logo][logo] Caravel


[![PEP compatible](http://pepkit.github.io/img/PEP-compatible-green.svg)](http://pepkit.github.io)

`Caravel` provides a web interface to interact with your [PEP-formatted projects](http://pepkit.github.io). `Caravel` lets you submit jobs to any cluster resource manager, monitor jobs, summarize results, and browse project summary web pages. `Caravel` is a local web GUI for [looper](https://code.databio.org/looper/) build with [flask](http://flask.pocoo.org/).

## Installing

Release versions are posted on the GitHub [caravel releases page](https://github.com/databio/caravel/releases). You can install the latest release directly from GitHub using `pip`:

```bash
pip install --user caravel
```

Update `caravel` with:

```bash
pip install --user --upgrade caravel
```
## Hello, world!

From within the root of the cloned repository

```bash
caravel -c example_config.yaml
```

The `example_config.yaml` file is a simple configuration file that points to your PEPs. See [how to configure caravel](configure-caravel).

## Setup and configuration

You can avoid passing the a config file with `-c` if you set environment variable `$CARAVEL` to point to a [YAML file](http://yaml.org) with a hyphen-bulleted list of [PEP config files](https://pepkit.github.io/docs/project_config/), like this:

```yaml
projects:
  - path/to/project1_config.yaml
  - path/to/project2_config.yaml
```

