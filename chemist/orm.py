# -*- coding: utf-8 -*-
# flake8: noqa

from __future__ import unicode_literals
import __builtin__

import logging
import uuid
import inspect
import dateutil.parser
import datetime
from uuid import uuid4
from functools import partial
from decimal import Decimal

import sqlalchemy as db
from sqlalchemy import (
    create_engine,
    MetaData,
)


engine = None


def get_engine(uri=None):
    if not uri:
        return globals()['engine']

    return set_engine(uri)


def set_engine(uri):
    globals()['engine'] = create_engine(uri)
    return globals()['engine']


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

        cls.__columns__ = {c.name: c.type.python_type
                           for c in cls.table.columns}
        setattr(ORM, name, cls)
        super(ORM, cls).__init__(name, bases, attrs)
