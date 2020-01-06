# -*- coding: utf-8 -*-
import io
import os
import yaml

from pathlib import Path
from os.path import abspath, expanduser, isfile, join, relpath

LOOKUP_PATHS = [
    abspath('/etc/flask-app.yaml'),
    abspath(expanduser('~/.flask-app.yaml')),
]


class UndefinedFalback:
    """sentinel type, allows config fallbacks to be None.
    """


class ConfigKeyNotFound(Exception):
    """Raised when trying to use :py:func:`get` with an inexisting key and
    no explicit ``fallback`` value.
    """
    def __init__(self, key, parent):
        msg = (
            'the config key "{key}" was not found '
            'under "{parent}" and no fallback was provided.'
        )
        super(ConfigKeyNotFound, self).__init__(msg.format(**locals()))


class InvalidDictConfigError(Exception):
    """raised by :py:func:`get_dict` when the requested key is not a dictionary
    """
    def __init__(self, key, parent):
        msg = (
            'the config key "{key}" cannot be retrieved '
            'because its parent "{parent}" is not a dictionary'
        )
        super(InvalidDictConfigError, self).__init__(msg.format(**locals()))


class InvalidTypeConfigError(Exception):
    """raised when trying to retrieve a config key of a specific type, but
    the actual value is from a different one.
    """
    def __init__(self, key, expected_type, value_type):
        msg = (
            'expected config key "{key}" to be a {expected_type} '
            'but instead got a {value_type}'
        )
        super(InvalidTypeConfigError, self).__init__(msg.format(**locals()))


class NoConfigFilesFound(Exception):
    """raised when none of the potential config paths have a valid file"""
    def __init__(self, paths):
        super(NoConfigFilesFound, self).__init__('no config was found in the paths: {}'.format(paths))


def current_path(*path):
    """constructs an absolute path based on the processe's cwd
    """
    return join(abspath(os.getcwd()), *path)


def get_lookup_paths():
    """
    :returns: a list of potential conf file lookup paths
    """
    initial = os.getenv('FLASK_APP_CONF_PATH')
    final = current_path('flask-app.yaml')
    return [initial] + list(LOOKUP_PATHS) + [final]


def determine_config_path():
    """
    :returns: a :py:class:`pathlib.Path` with the first valid file of the list of config paths (as returned by :py:func:`~flask_app.conf.get_lookup_paths`)
    """
    paths = get_lookup_paths()
    for result in filter(bool, paths):
        if isfile(str(result)):
            return Path(relpath(result))

    raise NoConfigFilesFound(paths)


def determine_config_dir():
    """
    :returns: a :py:class:`~pathlib.Path` pointing at the parent directory of the config file.
    """
    return Path(determine_config_path()).parent


def load(throw=False, fallback=UndefinedFalback):
    """loads the contents of the config at the given FLASK_APP_CONF_PATH

    Example:

    .. code:: python

       from flask_app import conf

       assert conf.get('dao', 's3', 'bucket_name') == 'newstore-development-dmz'
       assert conf.get('app', 'RESTPLUS_VALIDATE') is True

    :param path: positional args must be strings

    :returns: config under given key path
    """
    # if fallback is None:
    #     fallback = {}

    path = determine_config_path()
    if not isfile(str(path)):
        if throw:
            raise IOError('yaml config file does not exist: {}'.format(path))
        return {}

    with io.open(path, 'r') as stream:
        data = yaml.safe_load(stream)

    data['flaskapp_config_dir'] = str(determine_config_dir())
    return data


def get(*path, **kw):
    """retrieves a config by key path

    Example:

    .. code:: python

       from flask_app import conf

       assert conf.get('dao', 's3', 'bucket_name') == 'newstore-development-dmz'
       assert conf.get('logs_dir') == './logs/'

    :param path: positional args must be strings
    :param throw: boolean - whether to raise an exception or return a *falsy* value.
    :param fallback: a fallback value in case the config was not found

    :returns: config under given key path
    """
    # default to not throw:
    kw['throw'] = kw.pop('throw', False)
    fallback = kw.get('fallback', UndefinedFalback)
    throw = kw['throw']
    # load config from file
    config = load(**kw)

    trace = []
    for key in path:
        parent = '.'.join(trace)
        if not isinstance(config, dict):
            if fallback is UndefinedFalback:
                raise InvalidDictConfigError(key, parent)
            elif throw:
                raise ConfigKeyNotFound(key, parent)

            if fallback is UndefinedFalback:
                fallback = None
            return fallback

        if fallback is UndefinedFalback:
            fallback = None

        config = config.get(key) or fallback
        trace.append(key)

    return config


def key_representation(parts):
    """used in exceptions for describing the recursive path to the config
    """
    return ''.join("['{}']".format(p) for p in parts)


def get_dict(*args, **kw):
    """alias to :py:func:`~flask_app.conf.get(*args, **kw, fallback={})`

    :returns: **always** a :py:class:`dict`
    """
    kw['fallback'] = {}
    result = get(*args, **kw)
    key = key_representation(args)
    if not isinstance(result, dict):
        raise InvalidTypeConfigError(key, dict, repr(result))

    return result


def get_int(*args, **kw):
    """like :py:func:`get` but ensures that the final value is ``int``

    :raises: :py:exc:`InvalidTypeConfigError` if the value is not an int
    """
    kw['fallback'] = fallback = kw.get('fallback', 0)
    throw = kw.get('throw', False)

    value = get(*args, **kw)

    try:
        return int(value)
    except TypeError:
        key = key_representation(args)
        raise InvalidTypeConfigError(key, int, repr(value))

    except Exception:
        if throw:
            raise

    return fallback


def get_list(*args, **kw):
    """like :py:func:`get` but ensures that the final value is ``list``

    :raises: :py:exc:`InvalidTypeConfigError` if the value is not a list
    """
    kw['fallback'] = []
    result = get(*args, **kw)
    key = key_representation(args)
    if not isinstance(result, list):
        raise InvalidTypeConfigError(key, list, repr(result))

    return result
