""" Package exception types """

import abc

__all__ = ["CaravelError", "CaravelConfigError", "ConfigNotCompliantError"]

DOC_URL = "http://caravel.databio.org/en/latest/configure-caravel"


class CaravelError(Exception):
    """ Base exception type for this package """
    __metaclass__ = abc.ABCMeta


class MissingCaravelConfigError(CaravelError):
    """ Exception for missing caravel config file. """
    def __init__(self, msg):
        spacing = " " if msg[-1] in ["?", ".", "\n"] else "; "
        super(MissingCaravelConfigError, self).__init__(msg + spacing)


class CaravelConfigError(CaravelError):
    """ Exception for invalid caravel config file. """
    def __init__(self, msg):
        spacing = " " if msg[-1] in ["?", ".", "\n"] else "; "
        suggest = "For config format documentation please see " + DOC_URL
        super(CaravelConfigError, self).__init__(msg + spacing + suggest)


class ConfigNotCompliantError(CaravelError):
    """ The format of the config file does not match required version/standards """
    pass
