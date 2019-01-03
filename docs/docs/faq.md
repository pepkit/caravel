# FAQ


## Why isn't the ``caravel`` executable in my path?

> By default, Python packages are installed to ``~/.local/bin``. You can add this location to your path by appending it (``export PATH=$PATH:~/.local/bin``).

## How can I analyze my project interactively?
	
> `Caravel` uses the ``peppy`` package to model Project and Sample objects under the hood. These project objects are actually useful outside of looper. If you define your project using [pep format](http://pepkit.github.io), you can use the project models to instantiate an in memory representation of your project and all of its samples, without using looper. 

> If you're interested in this, you should check out the [peppy package](http://peppy.readthedocs.io/en/latest/models.html). All the documentation for model objects has moved there.
