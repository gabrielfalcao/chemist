# -*- coding: utf-8 -*-
# flake8: noqa

from __future__ import unicode_literals

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


ENGINE_REGISTRY = OrderedDict()
MODEL_REGISTRY = OrderedDict()


def get_first_available_engine():
    for engine in filter(bool, ENGINE_REGISTRY.values()):
        return engine

def get_engine(uri=None, key=None):
    if uri is None and key is None:
        key = '__default__'

    return get_or_create_engine(uri=uri, key=key)


def get_or_create_engine(uri, key=None):
    engine = ENGINE_REGISTRY.get(uri, ENGINE_REGISTRY.get(key)) or create_engine(uri)
    ENGINE_REGISTRY[key] = engine
    return engine


metadata = MetaData()

format_decimal = lambda num: '{0:.2f}'.format(num)
logger = logging.getLogger(__name__)


def generate_uuid():
    return bytes(uuid4().hex)

def now():
    return datetime.datetime.utcnow()



def DefaultTable(name, *fields):
    options = dict(
        # mysql_engine='InnoDB',
        # mysql_charset='utf8',
        # mysql_key_block_size="1024",
    )
    table = db.Table(
        name,
        metadata,
        *fields,
        **options
    )
    return table


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
