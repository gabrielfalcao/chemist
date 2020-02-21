# -*- coding: utf-8 -*-
import os
import re
import sys
import logging
import pathlib

from datetime import datetime
from collections import OrderedDict

from flask_app import conf
from flask_app.util import any_of


logging.getLogger().handlers = []

LOGGER_REGISTRY = OrderedDict()


DEFAULT_LEVEL_NAME = 'INFO'


def ansi_color256(code):
    return '\033[38;5;{}m'.format(code)


class ColorFormatter(logging.Formatter):
    # prints a nice output colored by log level
    COLORS = {
        'DEBUG': ansi_color256('76'),
        'INFO': ansi_color256('27'),
        'ERROR': ansi_color256('124'),
        'WARNING': ansi_color256('220'),
        'CRITICAL': ansi_color256('196'),
    }

    def format(self, record):
        """applies colors to log level names
        """
        level_name = record.levelname.upper()
        original = logging.Formatter.format(self, record)
        color = self.COLORS.get(level_name, '\033[37m')
        time = datetime.now().strftime("\033[37m[%Y-%m-%d %H:%M:%S]\033[0m")
        msg = "{time} {color}[{record.name}|{level_name}]\033[1;37m {original}\033[0m"
        return msg.format(**locals())


def determine_log_level():
    """attempts to retrieve the log level from the environment variable ``ACME_LOGLEVEL``
    """
    from_env_vars = os.getenv('ACME_LOGLEVEL')
    from_config = conf.get('logging', 'level')
    from_default = DEFAULT_LEVEL_NAME
    flag = any_of(
        from_config,
        from_env_vars,
        from_default,
    )
    found = re.search(r'(?P<name>debug|info|warning|error|critical|notset)', flag, re.IGNORECASE)
    if not found:
        # this should never happen, if it does let's log it all and trace the problem
        return logging.DEBUG

    level_name = found.group('name').upper()
    return getattr(logging, level_name, DEFAULT_LEVEL_NAME)


def get_formatter():
    if not sys.stdout.isatty():
        return logging.Formatter()

    return ColorFormatter()


def get_stream_handler(stream=sys.stderr):
    handler = logging.StreamHandler(stream)
    handler.setFormatter(get_formatter())
    return handler


def get_file_handler(filename):
    parent = pathlib.Path(filename).parent
    if not parent.exists():
        parent.mkdir(parents=True)

    return logging.FileHandler(filename)


def get_log_filename_from_conf(conf, prefix='acme.%Y-%m-%d.%H-%M'):
    logs_dir = conf.get('logging', 'directory', fallback=None)
    if not logs_dir or str(logs_dir).lower().strip() in ('none', 'null'):
        return None

    logs_path = pathlib.Path(logs_dir)
    filename = "{}.log".format(datetime.utcnow().strftime(prefix))
    return str(logs_path.joinpath(filename))


def get_logger(name, *args, **kw):
    """returns a :py:class:`logging.Logger` instance based on the
    configured :ref:`log level config`.
    """

    logger = logging.getLogger(name, *args, **kw)
    filename = get_log_filename_from_conf(conf)

    handlers = [get_stream_handler()]
    if filename:
        handlers.append(get_file_handler(filename))

    logger.handlers = handlers
    logger.setLevel(determine_log_level())
    LOGGER_REGISTRY[name] = logger
    return logger


def set_level(log_level):
    """sets the log level for all loggers to this number
    To see all available log levels check `the docs <https://docs.python.org/3/library/logging.html#logging-levels>`_

    :param name: the log level (integer)
    """
    root.setLevel(log_level)

    for name, logger in LOGGER_REGISTRY.items():
        logger.setLevel(log_level)


def set_level_by_name(name):
    """sets the log level for all loggers to this name.
    For a list of valid log level names check `the official python documentation <https://docs.python.org/3/library/logging.html#logging-levels>`_

    :param name: the log level name
    """
    level = getattr(logging, name, None)
    if level is None:
        raise RuntimeError('Invalid log level name "{}"'.format(name))

    set_level(level)


root = get_logger(None)
logger = get_logger('flask_app')
