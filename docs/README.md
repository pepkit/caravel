[logo]: img/logo_caravel.svg

# ![logo][logo] Caravel


[![PEP compatible](http://pepkit.github.io/img/PEP-compatible-green.svg)](http://pepkit.github.io)

`Caravel` provides a web interface to interact with your [PEP-formatted projects](http://pepkit.github.io). `Caravel` lets you submit jobs, monitor jobs, summarize results, and browse project summary web pages. It can connect to any cluster resource manager or container system. Think of `caravel` as a local web GUI for [looper](https://looper.databio.org) built with [flask](http://flask.pocoo.org/).

## Installing

Release versions are posted as [GitHub releases](https://github.com/databio/caravel/releases), or you can install from [pypi](https://pypi.org/project/caravel/) using `pip`:

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

The `example_config.yaml` file is a simple configuration file that points to your PEPs. You can avoid passing the config file with `-c` if you set environment variable `$CARAVEL`, explained in [how to configure caravel](configure-caravel).

