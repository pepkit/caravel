# <img src="caravel/static/caravel.svg" alt="caravel logo" height="70" align="left"/> caravel

[![PEP compatible](http://pepkit.github.io/img/PEP-compatible-green.svg)](http://pepkit.github.io)

`caravel` is a local web GUI for [looper](https://looper.readthedocs.io/). Caravel gives you a slick web interface to interact with your projects formatted as [PEPs](http://pepkit.github.io). You can use it to submit jobs to any cluster resource manager, monitor jobs, summarize results, and browse project summary web pages. `caravel` basically builds on top of `looper`, but uses the lightweight `flask` microframework to give you a web interface, making it even easier to manage your jobs for those who like pointy-clicky.

Documentation is hosted at [caravel.databio.org](http://caravel.databio.org) (source in the [/docs](/docs) folder).

## docker

[![Build Status](https://travis-ci.org/pepkit/caravel.svg?branch=master)](https://travis-ci.org/pepkit/caravel)

A docker image for running caravel is available through the dockerfile in this repository. To build the image:

```
docker build -t caravel_demo .
```

Run the container with `caravel --demo`:

```
docker run -p 5000:5000 caravel_demo caravel --demo
```
