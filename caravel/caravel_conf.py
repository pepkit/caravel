import yacman
import glob
from peppy import Project
from collections import Mapping
from .exceptions import *
import logging
from .const import *

logging.basicConfig(level=logging.INFO, format='%(levelname)s in CaravelConf: %(message)s')
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)


class CaravelConf(yacman.YacAttMap):
    """ Object used to interact with the caravel configuration file """
    def __init__(self, entries=None):
        """
        Create the config instance by with a filepath or key-value pairs.

        :param str | Iterable[(str, object)] | Mapping[str, object] entries:
            config filepath or collection of key-value pairs
        :raise refgenconf.MissingConfigDataError: if a required configuration
            item is missing
        :raise ValueError: if entries is given as a string and is not a file
        """
        super(CaravelConf, self).__init__(entries)
        config_path = entries if isinstance(entries, str) else ""
        projects = self.setdefault(CFG_PROJECTS_KEY, dict())
        if not isinstance(projects, dict):
            if projects:
                _LOGGER.warning("'{k}' value is a {t_old}, "
                                "not a {t_new}".format(k=CFG_PROJECTS_KEY, t_old=type(projects).__name__,
                                                       t_new=dict.__name__))
                # handle old caravel config format; reformat
                if isinstance(projects, list):
                    _LOGGER.info("Reformatting to the new config format: v{}".format(REQ_CFG_VERSION))
                    new_projects = dict()
                    for x in self[CFG_PROJECTS_KEY]:
                        new_projects.update({p: dict() for p in _process_project_path(x, config_path)})
                    self[CFG_PROJECTS_KEY] = new_projects
                else:
                    _LOGGER.info("Setting to empty {}".format(dict.__name__))
                    self[CFG_PROJECTS_KEY] = dict()
        try:
            version = self[CFG_VERSION_KEY]
        except KeyError:
            _LOGGER.warning("Config lacks '{}' key".format(CFG_VERSION_KEY))
            _LOGGER.info("Adding '{}' entry: {}".format(CFG_VERSION_KEY, REQ_CFG_VERSION))
            self[CFG_VERSION_KEY] = REQ_CFG_VERSION
        else:
            try:
                version = float(version)
            except ValueError:
                _LOGGER.warning("Cannot parse as numeric: {}".format(version))
            else:
                if version < REQ_CFG_VERSION:
                    msg = "This caravel config (v{}) is not compliant with v{} standards. " \
                          "To use it, please downgrade caravel: " \
                          "'pip install caravel==0.13.1'.".format(self[CFG_VERSION_KEY], str(REQ_CFG_VERSION))
                    raise ConfigNotCompliantError(msg)
                else:
                    _LOGGER.debug("Config version is compliant: {}".format(version))
        self.populate_project_names().write()

    def __bool__(self):
        minkeys = set(self.keys()) == {CFG_PROJECTS_KEY}
        return not minkeys or bool(self[CFG_PROJECTS_KEY])

    __nonzero__ = __bool__

    def update_projects(self, project, data=None):
        """
        Updates the project in CaravelConf object at any level. If the requested project is missing, it will be added

        :param str project: project to be added/updated
        :param Mapping data: data to be added/updated
        :return CaravelConf: updated object
        """
        if _check_insert_data(project, str, "project"):
            self[CFG_PROJECTS_KEY].setdefault(project, dict())
            if _check_insert_data(data, Mapping, "data"):
                self[CFG_PROJECTS_KEY][project].update(data)
        return self

    def remove_project(self, path):
        """
        Removes project by path

        :param str path: path of the project to be deleted
        :return CaravelConf: updated object
        """
        if path in self[CFG_PROJECTS_KEY]:
            del self[CFG_PROJECTS_KEY][path]
        else:
            _LOGGER.info("{} not found".format(path))
        return self

    def filter_missing(self):
        """
        Filters out projects that are missing

        :return CaravelConf: updated object
        """
        for p in self.list_missing_projects():
            self.remove_project(p)
        return self

    def list_projects(self):
        """
        Lists projects config paths

        :return list[str]: projects config paths
        """
        return self[CFG_PROJECTS_KEY].keys()

    def list_missing_projects(self):
        """
        Get the list of non-existent project configs

        :return list[str]: missing project configs
        """
        return [project for project in self.list_projects() if not os.path.exists(project)]

    def populate_project_names(self):
        """
        Populate project names for for every entry in CaravelConf.projects

        :return CaravelConf: object with populated project names
        """
        for path in self[CFG_PROJECTS_KEY].keys():
            try:
                self.update_projects(path, {CFG_PROJECT_NAME_KEY: Project(path).name})
            except Exception as e:
                _LOGGER.warning("Encountered '{}'\nCould not update name attr for '{}'".format(e.__class__.__name__,
                                                                                               path))
                self.update_projects(path, {CFG_PROJECT_NAME_KEY: None})
        return self


def _check_insert_data(obj, datatype, name):
    """ Checks validity of an object """
    if obj is None:
        return False
    if not isinstance(obj, datatype):
        raise TypeError("{} must be {}; got {}".format(name, datatype.__name__, type(obj).__name__))
    return True


def _process_project_path(path, rel):
    """ Expand path and make it relative to the config file """
    relative = os.path.join(os.path.dirname(rel), os.path.expanduser(os.path.expandvars(path)))
    matched = glob.glob(relative) or relative
    return matched if isinstance(matched, list) else [matched]
