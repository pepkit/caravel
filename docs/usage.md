# Usage reference


Here you can see the command-line usage instructions for `caravel`:


`caravel --help`:
```
caravel version: 0.13.1dev
looper version: 0.12.1
usage: caravel [-h] [-V] [-c CONFIG] [-p PORT] [-d] [--demo]

caravel - run a web interface for looper

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -c CONFIG, --config CONFIG
                        Config file (YAML). If not provided the environment
                        variable CARAVEL will be used instead. (default: None)
  -p PORT, --port PORT  The port the webserver should be run on. (default:
                        5000)
  -d, --dbg             Use this option if you want to enter the debug mode.
                        Unsecured. (default: False)
  --demo                Run caravel with demo data. (default: False)

See docs at: http://code.databio.org/caravel/

```
