# -*- coding: utf-8 -*-
import sqlalchemy as db

from uuid import uuid4
from functools import partial

from chemist.exceptions import InvalidColumnName
from chemist.exceptions import InvalidQueryModifier


def escape_query(query, escape='#'):
    for c in ('%', '_', '/'):
        query = query.replace(c, '{}{}'.format(escape, c))
    return query


class Manager(object):
    """
    """

    def __init__(self, model_klass, engine):
        self.model = model_klass
        self.engine = engine

    def from_result_proxy(self, proxy, result):
        """Creates a new instance of the model given
        an instance of :py:class:`sqlalchemy.engine.ResultProxy`"""
        if not result:
            return None

        data = dict(zip(proxy.keys(), result))
        return self.model(engine=self.engine, **data)

    def many_from_result_proxy(self, proxy):
        Models = partial(self.from_result_proxy, proxy)
        return list(map(Models, proxy.fetchall()))

    def create(self, **data):
        """Creates a new model and saves it to MySQL"""
        colmeta = getattr(self.model, '__columns__', {})
        cols = colmeta.keys()
        if 'uuid' in cols and 'uuid' not in data:
            data['uuid'] = uuid4().hex

        instance = self.model(engine=self.engine, **data)
        return instance.save()

    def get_or_create(self, **data):
        """Tries to get a model from the database that would match the
        given keyword-args through :py:meth:`Manager.find_one_by`. If not
        found, a new instance is created in the database through
        :py:meth:`Manager.create`"""
        instance = self.find_one_by(**data)
        if not instance:
            instance = self.create(**data)

        return instance

    def generate_query(
            self, order_by=None, limit_by=None, offset_by=None, **kw):
        """Queries the table with the given keyword-args and
        optionally a single order_by field."""
        query = self.model.table.select()
        for field, value in kw.items():
            if callable(value):
                value = value()

            if hasattr(self.model.table.c, field):
                query = query.where(getattr(self.model.table.c, field) == value)
            elif '__' in field:
                field, modifier = field.split('__', 1)
                f = getattr(self.model.table.c, field)
                if modifier == 'startswith':
                    query = query.where(f.startswith(value))
                elif modifier == 'contains':
                    contains = f.contains(escape_query(value), escape='#')
                    query = query.where(contains)
                else:
                    msg = '"{}" is in invalid query modifier.'.format(modifier)
                    raise InvalidQueryModifier(msg)
            else:
                msg = 'The field "{}" does not exist.'.format(field)
                raise InvalidColumnName(msg)

        if isinstance(limit_by, (float, int)):
            query = query.limit(limit_by)

        if isinstance(offset_by, (float, int)):
            query = query.offset(offset_by)

        # Order the results
        db_order = db.desc
        if order_by:
            if order_by.startswith('+'):
                order_by = order_by[1:]
                db_order = db.asc
            elif order_by.startswith('-'):
                order_by = order_by[1:]

        query = query.order_by(db_order(
            getattr(self.model.table.c, order_by or self.model.get_pk_name())
        ))

        return query

    def prepare_where_clause(self, *expressions, order_by=None):
        table = self.model.table
        query = table.select()
        for exp in expressions:
            query = query.where(exp)

        if isinstance(order_by, tuple):
            query = query.order_by(*order_by)
        elif order_by is not None:
            raise TypeError('order_by must be a tuple of SQLAlchemy columns optionally wrapped in asc/desc modifiers')

        return query

    def where_many(self, *expressions, order_by=None):
        query = self.prepare_where_clause(*expressions, order_by=order_by)
        return self.many_from_query(query)

    def where_one(self, *expressions, order_by=None):
        query = self.prepare_where_clause(*expressions, order_by=order_by)
        return self.one_from_query(query)

    def query_by(self, **kwargs):
        """This method is used internally and is not consistent with the other
        ORM methods by not returning a model instance."""
        conn = self.get_connection()
        query = self.generate_query(**kwargs)
        proxy = conn.execute(query)
        return proxy

    def many_from_query(self, query):
        conn = self.get_connection()
        proxy = conn.execute(query)
        return self.many_from_result_proxy(proxy)

    def one_from_query(self, query):
        conn = self.get_connection()
        proxy = conn.execute(query)
        return self.from_result_proxy(proxy, proxy.fetchone())

    def find_one_by(self, **kw):
        """Find a single model that could be found in the database and
        match all the given keyword-arguments"""
        proxy = self.query_by(**kw)
        return self.from_result_proxy(proxy, proxy.fetchone())

    def find_by(self, **kw):
        """Find a list of models that could be found in the database
        and match all the given keyword-arguments"""
        proxy = self.query_by(**kw)
        Models = partial(self.from_result_proxy, proxy)
        return list(map(Models, proxy.fetchall()))

    def all(self, limit_by=None, offset_by=None):
        """Returns all existing rows as Model"""
        return self.find_by(
            limit_by=limit_by,
            offset_by=offset_by,
        )

    def total_rows(self, field_name=None, **where):
        """Gets the total number of rows in the table"""
        field_name = field_name or self.model.get_pk_name()
        conn = self.get_connection()
        query = self.model.table.count()
        for key, value in where.items():
            field = getattr(self.model.table.c, key, None)
            if field is not None:
                query = query.where(field == value)

        proxy = conn.execute(query)

        return proxy.scalar()

    def get_connection(self):
        return self.engine.connect()
