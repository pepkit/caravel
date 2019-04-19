[logo]: img/logo_caravel.svg

# ![logo][logo] Caravel


[![PEP compatible](http://pepkit.github.io/img/PEP-compatible-green.svg)](http://pepkit.github.io)

`Caravel` provides a web interface to interact with your [PEP-formatted projects](http://pepkit.github.io). `Caravel` lets you submit jobs to any cluster resource manager, monitor jobs, summarize results, and browse project summary web pages. `Caravel` is a local web GUI using [flask](http://flask.pocoo.org/) for [looper](https://code.databio.org/looper/). 

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

* Set environment variable `$CARAVEL` to point to a YAML file formatted as shown below:

```yaml
projects:
  - path/to/project1_config.yaml
  - path/to/project2_config.yaml
```

## Run a web server

From within the root of the cloned repository

**Run like**:

```bash
caravel
```
if you have the `$CARAVEL` environment variable pointing to a list of project config files.

**Or like**:

```bash
caravel -c example_caravel.yaml
```
to point directly to a file declaring a list of project config filepaths.

Then point browser to the URL printed to your terminal.


**To run in debug/development mode**: 
```bash
caravel -c example_caravel.yaml -d
```
This will trigger the unsecured mode (no URL token required); point the browser to: http://127.0.0.1:5000 (by default)

## Run on a remote server

`Caravel` runs a very basic web server that lets you interact with it through the browser. What if you want to use a local browser, but connect to data and `looper` processing that lives on a remote server? You can use an `SSH` tunnel to map a local port to the remote port. It's quite simple, actually. When you `ssh` into the server, you use the `-L` flag to map the port like this:

```bash
ssh -L 5000:localhost:5000 user@server
```

Since `flask` (and `caravel`) uses port 5000 by default, this maps your localhost port 5000 to the server port 5000. You can now access the `caravel` GUI using your local web browser, pointing at: `http://localhost:5000`.

So a complete one-line command to run `caravel` remotely with a local web GUI would be something like this:

```bash
ssh -L 5000:localhost:5000 user@server "caravel -c caravel/example_caravel.yaml"
```
alternatively, to use other port, run like:

```bash
ssh -L 5001:localhost:5001 user@server "caravel -c caravel/example_caravel.yaml -p 5001"
```
## Security in `caravel`

`Caravel` uses an authentication token printed to your terminal to provide security. This way others are not able to connect to your `caravel` session and execute `looper` commands as _you_ on the remote server. 

By default the token is randomly generated upon `caravel` launch, but can be also set in the `.token_caravel` dotfile like:

```yaml
token: ABCD1234
```

Keep in mind that this is a less secure way of authentication as the token is exposed to ones that have the access to the `.token_caravel` file. Therefore make sure to set proper read permissions for this file.

## Verbosity of `caravel`

Both `looper` and `caravel` logging levels can be changed by toggling the debug mode at the server launch (`-d`, `--dbg` options). 
By default all the errors, warnings and information are displayed. The debug logs are activated when in debug mode.