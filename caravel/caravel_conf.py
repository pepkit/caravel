import datetime
import glob
from abc import ABC
from collections import Mapping

from flask import current_app
from looper import Project
from peppy.exceptions import MissingSubprojectError
from yacman import YacAttMap

from .const import *
from .exceptions import *


# import logging
# _LOGGER = logging.getLogger(__name__)


class CaravelConf(YacAttMap, ABC):
    """ Object used to interact with the caravel configuration file """
    def __init__(self, filepath=None, entries=None, writable=False, wait_max=10):
        """
        Create the config instance by with a filepath or key-value pairs.

        :param str | Iterable[(str, object)] | Mapping[str, object] entries:
            config filepath or collection of key-value pairs
        :raise refgenconf.MissingConfigDataError: if a required configuration
            item is missing
        :raise ValueError: if entries is given as a string and is not a file
        """
        super(CaravelConf, self).__init__(filepath=filepath, entries=entries, writable=writable, wait_max=wait_max)
        # config_path = entries if isinstance(entries, str) else ""
        projects = self.setdefault(CFG_PROJECTS_KEY, dict())
        if not isinstance(projects, dict):
            current_app.logger.warning("'{k}' value is a {t_old}, "
                                       "not a {t_new}".format(k=CFG_PROJECTS_KEY, t_old=type(projects).__name__,
                                                              t_new=dict.__name__))
            # handle old caravel config format; reformat
            if isinstance(projects, list):
                current_app.logger.info("Reformatting to the new config format: v{}".format(REQ_CFG_VERSION))
                new_projects = dict()
                for x in self[CFG_PROJECTS_KEY]:
                    new_projects.update({p: dict() for p in _process_project_path(x, self._file_path)})
                self[CFG_PROJECTS_KEY] = new_projects
            else:
                current_app.logger.info("Setting '{}' to empty {}".format(CFG_PROJECTS_KEY, dict.__name__))
                self[CFG_PROJECTS_KEY] = dict()
        try:
            version = self[CFG_VERSION_KEY]
        except KeyError:
            current_app.logger.warning("Config lacks '{}' key".format(CFG_VERSION_KEY))
            current_app.logger.info("Adding '{}' entry: {}".format(CFG_VERSION_KEY, REQ_CFG_VERSION))
            self[CFG_VERSION_KEY] = REQ_CFG_VERSION
        else:
            try:
                version = float(version)
            except ValueError:
                current_app.logger.warning("Cannot parse as numeric: {}".format(version))
            else:
                if version < REQ_CFG_VERSION:
                    msg = "This caravel config (v{}) is not compliant with v{} standards. " \
                          "To use it, please downgrade caravel: " \
                          "'pip install caravel==0.13.1'.".format(self[CFG_VERSION_KEY], str(REQ_CFG_VERSION))
                    raise ConfigNotCompliantError(msg)
                else:
                    current_app.logger.debug("Config version is compliant: {}".format(version))

    def __bool__(self):
        minkeys = set(self.keys()) == {CFG_PROJECTS_KEY}
        return not minkeys or bool(self[CFG_PROJECTS_KEY])

    __nonzero__ = __bool__

    def populate_project_metadata(self, attr_func=PROJECT_MDATA_FUN, paths=None, sp=None, clear=False):
        """
        Populate project metadata attributes for every entry in CaravelConf.projects.
        If the paths argument is not provided or it's an empty list, all the list projects names will be updated.

        :param Mapping[str,function(looper.Project) -> Any] attr_func: a Mapping of metadata attribute and
            corresponding lambda expression to extract it from a peppy.Project object
        :param list[str] | str paths: list of paths to the project config files which names should be updated
        :param list[str] | str sp: name of the subproject to populate the data for
        :param bool clear: whether specified project/subproject metadata should be removed
        :return: CaravelConf: object with populated project attributes
        """

        def _update_project_attrs(af_mapping, proj, subproj=None):
            """
            An internal function that populates the project/subproject attribute data.
            If no subproject provided, the main project's attribute data is updated.

            :param Mapping[str,function(looper.Project) -> Any] af_mapping: a Mapping of metadata attribute and
                corresponding lambda expression to extract it from a peppy.Project object
            :param looper.Project proj: project update the attributes for
            :param str subproj: subproject update the attributes for
            attribute and corresponding lambda expression to extract it from a peppy.Project object
            """
            for a, f in af_mapping.items():
                try:
                    self.update_projects(path=path, sp=subproj, data={a: f(proj)})
                except Exception as e:
                    current_app.logger.warning("Encountered '{}' -- Could not update '{}' attr for '{}'"
                                               .format(e.__class__.__name__, a, path))
                    self.update_projects(path=path, sp=subproj, data={a: None})

        sp_choice = sp
        if isinstance(paths, str) and os.path.isfile(paths):
            paths = [paths]
        if isinstance(sp, str):
            sp = [sp]
        if not isinstance(paths, (list, type(None))):
            raise TypeError("paths argument has to be a list, got {}".format(type(paths).__name__))
        if not isinstance(sp, (list, type(None))):
            raise TypeError("subprojects argument has to be a list, got {}".format(type(sp).__name__))
        paths = paths if paths is not None else self[CFG_PROJECTS_KEY].keys()
        for path in paths:
            if not os.path.exists(path):
                current_app.logger.debug("path '{}' does not exist, skipping metadata update".format(path))
                continue
            if clear:
                self.update_projects(path=path, clear=True)
                continue
            p = Project(path)
            _update_project_attrs(af_mapping=attr_func, proj=p)
            try:
                sp = sp if sp is not None else p.subprojects.keys()
            except AttributeError:
                current_app.logger.debug("No subprojects defined for: {}".format(path))
            else:
                for i in sp:
                    try:
                        p.activate_subproject(subproject=i)
                        _update_project_attrs(af_mapping=attr_func, proj=p, subproj=i)
                    except MissingSubprojectError:
                        current_app.logger.warning("Nonexistent project:subproject combination '{}:{}'. "
                                                   "Skipping".format(path, i))
            sp = sp_choice
        return self

    def project_date(self, paths, sp=None):
        """
        Add current date and time to the selected project/subproject section of the CaravelConf object

        :param list[str] | str paths: path to the project config of interest
        :param str sp: name of the subproject
        :return: CaravelConf: object with populated date
        """
        return self.populate_project_metadata(
            {"last_modified": lambda p: datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}, paths, sp=sp)

    def update_projects(self, path, sp=None, data=None, clear=False):
        """
        Updates the project in CaravelConf object at any level. If the requested project is missing, it will be added.
        Set the remove arg to True to remove all the metadata for the selected project

        :param str path: project to be added/updated
        :param str sp: subproject to be added/updated
        :param Mapping data: data to be added/updated
        :param bool clear: whether the keys for the selected project:subproject combination should be removed
        :return CaravelConf: updated object
        """
        def _remove_keys_but_name_desc(mapping):
            """ removes all the keys from the mapping but the 'name' key """
            for k in mapping.keys():
                if k in mapping and k not in (CFG_PROJECT_NAME_KEY, CFG_PROJECT_DESC_KEY):
                    del mapping[k]
        if check_insert_data(path, str, "project"):
            self[CFG_PROJECTS_KEY].setdefault(path, dict())
            if sp:
                check_insert_data(sp, str, "sp")
                self[CFG_PROJECTS_KEY][path].setdefault(CFG_SUBPROJECTS_KEY, dict())
                self[CFG_PROJECTS_KEY][path][CFG_SUBPROJECTS_KEY].setdefault(sp, dict())
                if check_insert_data(data, Mapping, "data"):
                    self[CFG_PROJECTS_KEY][path][CFG_SUBPROJECTS_KEY][sp].update(data)
                elif clear:
                    _remove_keys_but_name_desc(self[CFG_PROJECTS_KEY][path][CFG_SUBPROJECTS_KEY][sp])
            else:
                if check_insert_data(data, Mapping, "data"):
                    self[CFG_PROJECTS_KEY][path].update(data)
                elif clear:
                    _remove_keys_but_name_desc(self[CFG_PROJECTS_KEY][path])
        return self

    def remove_project(self, path, sp=None):
        """
        Removes project/subproject by path/name

        :param str path: path of the project to be deleted
        :param str sp: name of the subproject to be deleted
        :return CaravelConf: updated object
        """
        if path in self[CFG_PROJECTS_KEY]:
            if sp:
                if sp in self[CFG_PROJECTS_KEY][path][CFG_SUBPROJECTS_KEY]:
                    del self[CFG_PROJECTS_KEY][path][CFG_SUBPROJECTS_KEY][sp]
                    if not bool(len(self[CFG_PROJECTS_KEY][path][CFG_SUBPROJECTS_KEY].keys())):
                        current_app.logger.info("No more subprojs defined for '{}', "
                                                "removing '{}' section".format(path, CFG_SUBPROJECTS_KEY))
                        del self[CFG_PROJECTS_KEY][path][CFG_SUBPROJECTS_KEY]
                else:
                    current_app.logger.warning("'{}:{}' not found".format(path, sp))
            else:
                del self[CFG_PROJECTS_KEY][path]
        else:
            current_app.logger.warning("'{}' not found".format(path))
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


def check_insert_data(obj, datatype, name):
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
