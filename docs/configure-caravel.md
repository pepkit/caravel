# How to configure caravel

## The caravel configuration file

`Caravel` just needs a list of your [PEP-formatted](http://pepkit.github.io) projects, which you specify with a [YAML file](http://yaml.org) with a hyphen-bulleted list of [PEP config files](https://pepkit.github.io/docs/project_config/), like this:

```yaml
projects:
  - "path/to/project1_config.yaml"
  - "path/to/project2_config.yaml"
```

You can also use wildcards (`*`)  to add projects according to a pattern:

```yaml
projects:
  - "path/to/project1_config.yaml"
  - "path/to/project2_config.yaml"  
  - "other/path/to/PEPs/*/*_config.yaml"  # adds all matched projects
```

Paths should be either absolute or *relative to the caravel configuration file*.

## The `$CARAVEL` environment variable

You can avoid passing the configuration file with `-c` by putting that path into the `$CARAVEL` environment variable:

```console
export CARAVEL="/path/to/caravel.yaml"
```

This way you can start it up with nothing more than `caravel`.
