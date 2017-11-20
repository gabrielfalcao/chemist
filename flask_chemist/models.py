# -*- coding: utf-8 -*-
import __builtin__
import json
import nacl.secret
import nacl.utils
import inspect
import datetime
from decimal import Decimal
import dateutil.parser

from flask_chemist.orm import ORM
from flask_chemist.orm import get_engine
from flask_chemist.orm import format_decimal

from flask_chemist.managers import Manager

from flask_chemist.exceptions import FieldTypeValueError
from flask_chemist.exceptions import MultipleEnginesSpecified
from flask_chemist.exceptions import EngineNotSpecified
from flask_chemist.exceptions import InvalidColumnName
from flask_chemist.exceptions import InvalidModelDeclaration


class Model(object):
    '''
    '''
    __metaclass__ = ORM
    __primary_key_name__ = 'id'
    manager = Manager

    @classmethod
    def using(cls, engine):
        if engine is None:
            engine = get_engine()

        return cls.manager(cls, engine)

    create = classmethod(lambda cls, **data: cls.using(None).create(**data))
    get_or_create = classmethod(lambda cls, **data: cls.using(None).get_or_create(**data))
    query_by = classmethod(lambda cls, order_by=None, **kw: cls.using(None).query_by(order_by=order_by, **kw))
    find_one_by = classmethod(lambda cls, **kw: cls.using(None).find_one_by(**kw))
    find_by = classmethod(lambda cls, **kw: cls.using(None).find_by(**kw))
    all = classmethod(lambda cls, **kw: cls.using(None).all(**kw))
    total_rows = classmethod(lambda cls, **kw: cls.using(None).total_rows(**kw))
    get_connection = classmethod(lambda cls, **kw: cls.using(None).get_connection())
    many_from_query = classmethod(lambda cls, query: cls.using(None).many_from_query(query))
    one_from_query = classmethod(lambda cls, query: cls.using(None).one_from_query(query))

    def __init__(self, engine=None, **data):
        '''A Model can be instantiated with keyword-arguments that
        have the same keys as the declared fields, it will make a new
        model instance that is ready to be persited in the database.

        DO NOT overwrite the __init__ method of your custom model.

        There are 2 possibilities of customization of your model in
        construction time:

        * Implement a `preprocess(self, data)` method in your model,
        this method takes the dictionary that has the
        keyword-arguments given to the constructor and should return a
        dictionary with that data "post-processed" This ORM provides
        the handy optional method `initialize` that is always called
        in the end of the constructor.

        * Implement the `initialize(self)` method that will be always
          called after successfully creating a new model instance.
        '''
        Model = self.__class__
        module = Model.__module__
        name = Model.__name__
        columns = self.__columns__.keys()
        for key, value in data.items():
            data[key] = self.decrypt_attribute(key, value)

        preprocessed_data = self.preprocess(data)

        if not isinstance(preprocessed_data, dict):
            raise InvalidModelDeclaration(
                'The model `{0}` declares a preprocess method but '
                'it does not return a dictionary!'.format(name))

        self.__data__ = preprocessed_data

        self.engine = engine

        for k, v in data.iteritems():
            if k not in self.__columns__:
                msg = "{0} is not a valid column name for the model {2}.{1} ({3})"
                raise InvalidColumnName(msg.format(k, name, module, columns))

            if callable(v):
                v = v()

            setattr(self, k, v)

        self.initialize()

    def __repr__(self):
        return '<{0} id={1}>'.format(self.__class__.__name__, self.id)

    def preprocess(self, data):
        """Placeholder for your own custom preprocess method, remember
        it must return a dictionary"""
        return data

    def get_encryption_box_for_attribute(self, attr):
        keymap = dict(getattr(self, 'encryption', {}))
        if attr not in keymap:
            return

        key = keymap[attr]

        box = nacl.secret.SecretBox(key)
        return box

    def encrypt_attribute(self, attr, value):
        box = self.get_encryption_box_for_attribute(attr)
        if not box:
            return value

        nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
        return box.encrypt(str(value), nonce)

    def decrypt_attribute(self, attr, value):
        box = self.get_encryption_box_for_attribute(attr)
        if not box:
            return value

        try:
            return box.decrypt(value)
        except ValueError:
            return value

    def serialize_value(self, attr, value):
        col = self.table.columns[attr]

        if col.default and not value:
            if col.default.is_callable:
                value = col.default.arg(value)
            else:
                value = col.default.arg

        if isinstance(value, Decimal):
            return format_decimal(value)

        date_types = (datetime.datetime, datetime.date, datetime.time)
        if isinstance(value, date_types):
            return value.isoformat()

        if not value:
            return value

        data_type = self.__columns__.get(attr, None)
        builtins = dict(inspect.getmembers(__builtin__)).values()
        if data_type and not isinstance(value, data_type) and data_type in builtins:
            try:
                return data_type(value)
            except ValueError as e:
                raise FieldTypeValueError(self, attr, e)

        return value

    def deserialize_value(self, attr, value):
        value = self.decrypt_attribute(attr, value)

        date_types = (datetime.datetime, datetime.date)

        kind = self.__columns__.get(attr, None)
        if issubclass(kind, date_types) and not isinstance(value, kind) and value:
            return dateutil.parser.parse(value)

        return value

    def __setattr__(self, attr, value):
        if attr in self.__columns__:
            self.__data__[attr] = self.deserialize_value(attr, value)
            return

        return super(Model, self).__setattr__(attr, value)

    def to_dict(self):
        """pre-serializes the model, returning a dictionary with
        key-values.

        This method can be overwritten by subclasses at will.
        """
        return self.serialize()

    def serialize(self):
        """pre-serializes the model, returning a dictionary with
        key-values.

        This method is use by the to_dict() and only exists as a
        separate method so that subclasses overwriting `to_dict` can
        call `serialize()` rather than `super(SubclassName,
        self).to_dict()`
        """

        keys = self.__columns__.keys()
        return dict([(k, self.serialize_value(k, self.__data__.get(k))) for k in self.__columns__.keys()])

    def to_insert_params(self):
        pre_data = Model.serialize(self)
        data = {}

        for k, v in pre_data.items():
            data[k] = self.encrypt_attribute(k, v)

        primary_key_names = [x.name for x in self.table.primary_key.columns]
        keys_to_pluck = filter(lambda x: x not in self.__columns__, data.keys()) + primary_key_names

        # not saving primary keys, let's let the SQL backend to take
        # care of auto increment.

        # if we need fine tuning and allow manual primary key
        # definition, just go ahead and change this code and it's
        # tests :)
        for key in keys_to_pluck:
            data.pop(key)

        return data

    def to_json(self, indent=None):
        """Grabs the dictionary with the current model state returned
        by `to_dict` and serializes it to JSON"""
        data = self.to_dict()
        return json.dumps(data, indent=indent)

    def __getattr__(self, attr):
        if attr in self.__columns__.keys():
            value = self.__data__.get(attr, None)
            return self.serialize_value(attr, value)

        return super(Model, self).__getattribute__(attr)

    def delete(self):
        """Deletes the current model from the database (removes a row
        that has the given model primary key)
        """

        self.pre_delete()

        conn = self.get_engine().connect()

        result = conn.execute(self.table.delete().where(
            self.table.c.id == self.id))

        self.post_delete()
        return result

    def pre_delete(self):
        pass

    def post_delete(self):
        pass

    @property
    def is_persisted(self):
        return self.__class__.__primary_key_name__ in self.__data__.keys()

    def get_engine(self, input_engine=None):

        if not self.engine and not input_engine:
            raise EngineNotSpecified(
                "You must specify a SQLAlchemy engine object in order to "
                "do operations in this model instance: {0}".format(self))
        elif self.engine and input_engine:
            raise MultipleEnginesSpecified(
                "This model instance has a SQLAlchemy engine object already. "
                "You may not save it to another engine.")

        return self.engine or input_engine

    def save(self, input_engine=None):
        """Persists the model instance in the DB.
        It takes care of checking whether it already exists and should be just updated or if a new record should be created.
        """
        self.before_save()

        conn = self.get_engine(input_engine).connect()
        primary_key_column_name = self.__class__.__primary_key_name__
        mid = self.__data__.get(primary_key_column_name, None)
        if mid is None:
            res = conn.execute(
                self.table.insert().values(**self.to_insert_params()))

            self.__data__[primary_key_column_name] = res.inserted_primary_key[0]
            self.__data__.update(res.last_inserted_params())
        else:
            res = conn.execute(
                self.table.update().values(**self.to_insert_params()).where(self.table.c.id == mid))
            self.__data__.update(res.last_updated_params())

        return self

    def before_save(self):
        pass

    def refresh(self):
        new = self.find_one_by(id=self.id)
        self.set(**new.__data__)
        return self

    def set(self, **kw):
        """Sets multiple fields"""
        cols = self.__columns__.keys()

        for name, value in kw.items():
            if name not in cols:
                raise InvalidColumnName('{0}.{1}'.format(self, name))
            setattr(self, name, value)

        return self

    def update_and_save(self, **kw):
        """Sets multiple fields then saves them"""
        updated = self.set(**kw)
        return updated.save()

    def get(self, name, fallback=None):
        """Get a field value from the model"""
        return self.__data__.get(name, fallback)

    def initialize(self):
        """Dummy method to be optionally overwritten in the subclasses"""

    def __eq__(self, other):
        """Just making sure models are comparable to each other"""
        if self.id and other.id:
            return self.id == other.id

        keys = set(self.__data__.keys() + other.__data__.keys())

        return all(
            [self.__data__.get(key) == other.__data__.get(key)
             for key in keys if key != self.__class__.__primary_key_name__])
