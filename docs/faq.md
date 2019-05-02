# FAQ


## Why isn't the ``caravel`` executable in my path?

> By default, Python packages are installed to ``~/.local/bin``. You can add this location to your path by appending it (``export PATH=$PATH:~/.local/bin``).

## How can I analyze my project interactively?
	
> `Caravel` uses the ``peppy`` package to model Project and Sample objects under the hood. These project objects are actually useful outside of looper. If you define your project using [pep format](http://pepkit.github.io), you can use the project models to instantiate an in memory representation of your project and all of its samples, without using looper. 

> If you're interested in this, you should check out the [peppy package](http://peppy.readthedocs.io/en/latest/models.html). All the documentation for model objects has moved there.

## I'm getting [Errno 98] Address already in use.

> Caravel by default runs on port 5000. Something else may already be running on that port on your server. You can change the port by specifying `-p PORTNUM`. Try using 5001 or 5002. If you're forwarding a port from a server, you'll also need to change the port number in your `ssh` call.

## How to kill the `caravel` process running on the remote server

> Sometimes, when the `caravel` server is unintentionally closed, e.g. with `CTRL+C` (`SIGINT`) the process will occupy the port indefinetely. 
To kill the process first log in to the remote server and find out its `PID` with `lsof -i :<port number>`
>```
>mjs5kd@udc-ba34-36:/home/mjs5kd lsof -i :5001
>COMMAND    PID   USER   FD   TYPE    DEVICE SIZE/OFF NODE NAME
>caravel 109823 mjs5kd    4u  IPv4 587213669      0t0  TCP localhost.localdomain:commplex-link (LISTEN)
>```
> and then kill it with `kill <PID>`