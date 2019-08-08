# How to configure caravel

## The caravel configuration file

`Caravel` just needs a list of your [PEP-formatted](http://pepkit.github.io) projects, which you specify with a [YAML file](http://yaml.org) with a hyphen-bulleted list of [PEP config files](https://pepkit.github.io/docs/project_config/), like this:

```yaml
projects:
  - path/to/project1_config.yaml
  - path/to/project2_config.yaml
```

You can also use wildcards (`*`)  to add projects according to a pattern:

```yaml
projects:
  - path/to/project1_config.yaml
  - path/to/project2_config.yaml
  - other/path/to/PEPs/*/*_config.yaml  # adds all matched projects
```

Paths should be either absolute or *relative to the caravel configuration file*.

## New config format

Starting with v0.13.2 `caravel` uses the config file for project metadata management. Consequently, upon the server launch, the file formatted as presented above is reformatted so it is compliant with config version 0.2 standards.
One of the user facing benefits of this change is **the possibility to configure `caravel` preferences directly in the config**, like:
```yaml
projects:
  - path/to/project1_config.yaml
  - path/to/project2_config.yaml
preferences:
  status_check_interval: 3
  compute_package: local
```
 
### Config v0.2 example

```yaml
config_version: 0.2
projects:
  caravel/examples/caravel_demo/metadata/animals_config.yaml:
    project_description: This is an examplary project
  caravel/examples/caravel_demo/metadata/duplicated_config.yaml:
    project_description: This is another examplary project
preferences:
  status_check_interval: 3
  compute_package: local
```

Although the new configuration file format is much more flexible and powerful, the old format is still supported. Particularly because it is much easier to create it by hand. 

## The `$CARAVEL` environment variable

You can avoid passing the configuration file with `-c` by putting that path into the `$CARAVEL` environment variable:

```console
export CARAVEL="/path/to/caravel.yaml"
```

This way you can start it up with nothing more than `caravel`.
