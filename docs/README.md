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

You can now try running `caravel` on the command line: 

```bash
caravel -c example_config.yaml
```

The `example_config.yaml` file is a simple configuration file that points to your PEPs. See [how to configure caravel](configure-caravel).

