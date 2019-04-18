# Changelog

## v0.2 (*2019-04-18*)

Changed: 

  - Use logger instead of printing to the error for logging
  - Instead of having the optional `token` section in the config file 
  allow to use hidden `.caravel_token` to predefine the token
  - Change logging levels to 10 (debug) and 20 (info) in debug and normal modes, respectively

Added:

  - New `bootstrap` UI
  - Back button to each page
  - Compute environment configuration page
  - Deactivate subproject with a dedicated button
  - Use `divvy` for computing environment configuration
  - Display `looper` log in the terminal and in a separate page, when finished
  - `looper` and `peppy` versions assurance
  - New way of `caravel`, `looper` and `python` versions monitoring on the client side in the footer
  - Systematic HTML form elements determination based on `looper` arguments options
  - The port that the server will be run on can be determined manually from the CLI (`-p` and `--port` options)
  - Seamless integration with `looper` reporting module, the pages are displayed with `caravel`'s navbar and footer

## v0.1.1 (*2019-01-15*)

Changed:

  - Fixed a bug that prevented command options from populating (caravel now uses looper's command line parser)
  - Fixed a bug that required re-starting with token upon any errors.
  - Allow for activating subprojects using new `peppy` method.
  
Added:

  - Allow setting the authentication token in the caravel config file

## v0.1 (*2018-12-21*)

Added:

  - First semi-functional release of caravel.

