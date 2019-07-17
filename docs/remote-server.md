# How to run on a remote server

`Caravel` runs a very basic web server that lets you interact with it through the browser. What if you want to use a local browser, but connect to data and `looper` processing that lives on a remote server? You can use an `SSH` tunnel to map a local port to the remote port. It's quite simple, actually. When you `ssh` into the server, you use the `-L` flag to map the port like this:

```bash
ssh -L 5000:localhost:5000 user@server
```

Since `flask` (and `caravel`) uses port 5000 by default, this maps your localhost port 5000 to the server port 5000. You can now access the `caravel` GUI using your local web browser, pointing at: `http://localhost:5000`.

So a complete one-line command to run `caravel` remotely with a local web GUI would be something like this:

```bash
ssh -L 5000:localhost:5000 user@server "caravel -c caravel/caravel_demo.yaml"
```
alternatively, to use another port, run like:

```bash
ssh -L 5001:localhost:5001 user@server "caravel -c caravel/caravel_demo.yaml -p 5001"

```