# -*- coding: utf-8 -*-
# flake8: noqa

from __future__ import unicode_literals
import os
import warnings
from six.moves import builtins as __builtin__
import logging
import uuid
import inspect
import dateutil.parser
import datetime
from uuid import uuid4
from functools import partial
from decimal import Decimal
from collections import OrderedDict
import sqlalchemy as db
from sqlalchemy import (
    create_engine,
    MetaData,
)


MODEL_REGISTRY = OrderedDict()


format_decimal = lambda num: '{0:.2f}'.format(num)
logger = logging.getLogger(__name__)


def generate_uuid():
    return bytes(uuid4().hex)

def now():
    return datetime.datetime.utcnow()


def DefaultForeignKey(field_name, parent_field_name,
                      ondelete='CASCADE', nullable=False, **kw):
    return db.Column(field_name, db.Integer,
                     db.ForeignKey(parent_field_name, ondelete=ondelete),
                     nullable=nullable, **kw)


def PrimaryKey(name='id'):
    return db.Column(name, db.Integer, primary_key=True)

def AutoUUID(name='uuid'):
    return db.Column(name, db.String(32), default=generate_uuid)

def is_builtin_model(target):
    return target.__module__.startswith('chemist.') and target.__name__ in ('ORM', 'Model')


class ORM(type):
    """metaclass for :py:class:`chemist.models.Model`
    """

    def __init__(cls, name, bases, attrs):
        if is_builtin_model(cls):
            return

        if not is_builtin_model(cls) and not hasattr(cls, 'table'):
            raise TypeError('{} must have a table attribute defined at the class level'.format(cls))


        columns = {c.name: c.type.python_type
                           for c in cls.table.columns}
        cls.__columns__ = columns
        attrs['__columns__'] = columns
        ORM.register_model_class(cls, columns)

        super(ORM, cls).__init__(name, bases, attrs)


    @staticmethod
    def determine_model_identity(cls):
        return '.'.join([cls.__module__, cls.__name__])

    @staticmethod
    def register_model_class(cls, columns):
        class_id = ORM.determine_model_identity(cls)
        MODEL_REGISTRY[class_id] = columns
        return cls

    @staticmethod
    def get_columns_for_model_class(cls):
        class_id = ORM.determine_model_identity(cls)
        return MODEL_REGISTRY.get(class_id, {}) or {}

    @staticmethod
    def get_columns_for_model_instance(instance):
        return ORM.get_columns_for_model_class(instance.__class__)


class Context(object):
    """Context is a system component that keeps track of multiple engines,
    switch between them and manage their lifecycle.

    It also provides a :py:class:`sqlalchemy.MetaData` instance that is automatically bound to

    Its purpose is to leverage quicky swapping the engine between "unit" tests.
    """
    def __init__(self, default_uri:str=None):
        self.default_uri = default_uri or os.getenv('CHEMIST_SQLALCHEMY_URI')
        self.engines = OrderedDict()
        self.metadata = MetaData()

    def set_default_uri(self, uri: str):
        self.default_uri = uri
        self.metadata.bind = self.get_default_engine()
        return self.metadata

    def get_or_create_engine(self, uri, *args, **kwargs):
        engine = self.engines.get(uri, self.engines.get(uri)) or create_engine(uri, **kwargs)
        self.engines[uri] = engine
        return engine

    @property
    def engine(self):
        return self.get_default_engine()

    def get_engine(self, uri=None):
        if self.uri:
            return self.get_or_create_engine(uri)

        return self.get_default_engine()

    def get_default_engine(self):
        return self.get_or_create_engine(self.default_uri)

    def DefaultTable(self, name, *fields):
        options = dict(
            # mysql_engine='InnoDB',
            # mysql_charset='utf8',
            # mysql_key_block_size="1024",
        )
        table = db.Table(
            name,
            self.metadata,
            *fields,
            **options
        )
        return table


default_context = Context()

metadata = default_context.metadata
get_or_create_engine = default_context.get_or_create_engine
DefaultTable = default_context.DefaultTable


def get_first_available_engine():
    for engine in filter(bool, default_context.engines.values()):
        return engine

def get_engine(uri=None, key=None):
    if not uri:
        return default_context.get_default_engine()

    if key:
        warnings.warn("{} will be deprecated in the next minor version of chemist. Pass a key for a Context instead".format(key), DeprecationWarning)

    return get_or_create_engine(uri=uri)


def set_default_uri(uri):
    default_context.set_default_uri(uri)
    return default_context.get_default_engine()
