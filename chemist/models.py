# -*- coding: utf-8 -*-
from six.moves import builtins as __builtin__
from six import PY2

import re
import json
import nacl.secret
import nacl.utils
import inspect
import datetime
from decimal import Decimal
from collections import OrderedDict
from six import with_metaclass
import dateutil.parser

from chemist.orm import ORM
from chemist.orm import get_engine
from chemist.orm import format_decimal

from chemist.managers import Manager

from chemist.exceptions import FieldTypeValueError
from chemist.exceptions import MultipleEnginesSpecified
from chemist.exceptions import EngineNotSpecified
from chemist.exceptions import InvalidColumnName
from chemist.exceptions import InvalidModelDeclaration


if PY2:
    string_types = (basestring, )
else:
    string_types = (str, )



class Model(with_metaclass(ORM, object)):
    """Super-class of active record models.

    **Example:**

    ::

      class BlogPost(Mode):
          table = db.Table(
              'blog_post',
              metadata,
              db.Column('id', db.Integer, primary_key=True),
              db.Column('title', db.Unicode(200), nullable=False),
              db.Column('slug', db.Unicode(200), nullable=False),
              db.Column('content', db.UnicodeText, nullable=False),
         )

          def preprocess(self, data):
              # always derive slug from title
              data['slug'] = slugify(data['title'])
              return data
    """

    manager = Manager

    @classmethod
    def using(cls, engine):
        if engine is None:
            engine = get_engine()

        elif isinstance(engine, string_types):
            engine = get_engine(uri=engine)

        return cls.manager(cls, engine)

    @classmethod
    def objects(cls):
        return cls.using(None)

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
    where_many = classmethod(lambda cls, *args, **kw: cls.using(None).where_many(*args, **kw))
    where_one = classmethod(lambda cls, *args, **kw: cls.using(None).where_one(*args, **kw))

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
        columns = self.__columns__

        for key, value in data.items():
            data[key] = self.decrypt_attribute(key, value)

        preprocessed_data = self.preprocess(data)

        if not isinstance(preprocessed_data, dict):
            raise InvalidModelDeclaration(
                'The model `{0}` declares a preprocess method but '
                'it does not return a dictionary!'.format(name))

        self.__data__ = preprocessed_data

        self.engine = engine

        for k, v in data.items():
            if k not in self.__columns__:
                msg = "{0} is not a valid column name for the model {2}.{1} ({3})"
                raise InvalidColumnName(msg.format(k, name, module, sorted(columns.keys())))

            if callable(v):
                v = v()

            setattr(self, k, v)

        self.initialize()

    def __repr__(self):
        return '<{0} {1}={2}>'.format(self.__class__.__name__, self.get_pk_name(), self.get_pk_value())

    def preprocess(self, data):
        """Placeholder for your own custom preprocess method, remember
        it must return a dictionary.

        ::

          class BlogPost(Mode):
              table = db.Table(
                  'blog_post',
                  metadata,
                  db.Column('id', db.Integer, primary_key=True),
                  db.Column('title', db.Unicode(200), nullable=False),
                  db.Column('slug', db.Unicode(200), nullable=False),
                  db.Column('content', db.UnicodeText, nullable=False),
             )

              def preprocess(self, data):
                  # always derive slug from title
                  data['slug'] = slugify(data['title'])
                  return data
        """
        return data

    def get_encryption_box_for_attribute(self, attr):
        keymap = dict(getattr(self, 'encryption', None) or {})
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

        **Example:**

        ::

          >>> post = BlogPost.create(title='Some Title', content='loren ipsum')
          >>> post.to_dict()
          {
            'id': 1,
            'title': 'Some Title',
            'slug': 'some-title',
          }
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

        keys = list(self.__columns__.keys())
        return dict([(k, self.serialize_value(k, self.__data__.get(k))) for k in self.__columns__.keys()])

    def to_insert_params(self):
        """utility method used internally to generate a dict with all the
        serialized values except primary keys.

        **Example:**

        ::

          >>> post = BlogPost.create(title='Some Title', content='loren ipsum')
          >>> post.to_insert_params()
          {
            'title': 'Some Title',
            'slug': 'some-title',
          }

        """
        pre_data = Model.serialize(self)
        data = OrderedDict()

        for k, v in pre_data.items():
            data[k] = self.encrypt_attribute(k, v)

        primary_key_names = [x.name for x in self.table.primary_key.columns]
        keys_to_pluck = list(filter(lambda x: x not in self.__columns__, data.keys())) + primary_key_names

        # not saving primary keys, let's let the SQL backend to take
        # care of auto increment.

        # if we need fine tuning and allow manual primary key
        # definition, just go ahead and change this code and it's
        # tests :)
        for key in keys_to_pluck:
            data.pop(key)

        return data

    def to_json(self, indent=None, sort_keys=True, **kw):
        """Grabs the dictionary with the current model state returned
        by `to_dict` and serializes it to JSON"""
        data = self.to_dict()
        return json.dumps(data, indent=indent, sort_keys=sort_keys, **kw)

    def __getattr__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            columns = list(self.__columns__.keys())
            if attr in columns:
                value = self.__data__.get(attr, None)
                return self.serialize_value(attr, value)

    def delete(self):
        """Deletes the current model from the database (removes a row
        that has the given model primary key)
        """

        self.pre_delete()

        conn = self.get_engine().connect()

        result = conn.execute(self.table.delete().where(
            getattr(self.table.c, self.get_pk_name()) == self.get_pk_value()
        ))

        self.post_delete()
        return result

    def pre_delete(self):
        """called right before executing a deletion.
        This method can be overwritten by subclasses in order to take any domain-related action
        """

    def post_delete(self):
        """called right after executing a deletion.
        This method can be overwritten by subclasses in order to take any domain-related action
        """

    @property
    def is_persisted(self):
        """boolean property that returns **True** if the primary key is set.
        This property **does not perform I/O against the database**
        """
        return self.get_pk_name() in self.__data__.keys()

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
        self.pre_save()

        conn = self.get_engine(input_engine).connect()
        primary_key_column_name = self.get_pk_name()
        mid = self.__data__.get(primary_key_column_name, None)
        if mid is None:
            values = self.to_insert_params()
            res = conn.execute(self.table.insert().values(**values))

            primary_keys = {
                primary_key_column_name: res.inserted_primary_key[0]
            }
            self.set(**dict(primary_keys))
            self.set(**dict(res.last_inserted_params()))
        else:
            res = conn.execute(
                self.table.update().values(**self.to_insert_params()).where(self.get_pk_col(primary_key_column_name) == mid))
            newdata = res.last_updated_params()
            for k in list(newdata.keys()):
                if k.endswith('_1'):
                    newdata[k[:-2]] = newdata.pop(k)

            self.set(**dict(newdata))

        self.post_save()

        return self

    def pre_save(self):
        """called right before executing a save.
        This method can be overwritten by subclasses in order to take any domain-related action
        """

    def post_save(self):
        """called right after executing a save.
        This method can be overwritten by subclasses in order to take any domain-related action
        """

    def refresh(self):
        """updates the current record with fresh values retrieved by
        :py:meth:`find_one_by` and also returns a brand new instance.

        .. note:: any unsaved changes in the model will be lost upon
                  calling this method.

        """
        params = {}
        params[self.get_pk_name()] = self.get_pk_value()
        new = self.find_one_by(**params)
        self.set(**new.__data__)
        return new

    def set(self, **kw):
        """Sets multiple fields, does not perform a save operation
        """
        cols = self.__columns__.keys()
        pk_regex = re.compile(r'^{}_\d+$'.format(self.get_pk_name))

        for name, value in kw.items():
            if pk_regex.match(name):
                continue

            if name not in cols:
                raise InvalidColumnName('{0}.{1}'.format(self, name))
            setattr(self, name, value)
            self.__data__[name] = value

        return self

    def update_and_save(self, **kw):
        """Sets multiple fields then saves them"""
        updated = self.set(**kw)
        return updated.save()

    def get(self, name, fallback=None):
        """Get a field value from the model"""
        return self.__data__.get(name, fallback)

    def initialize(self):
        """Dummy method to be optionally overwritten in the subclasses.
        Gets automatically called once a model instance is constructed.
        """

    def __eq__(self, other):
        """Just making sure models are comparable to each other"""

        matches_pk = all([
            type(self) == type(other),
            self.get_pk_name() == other.get_pk_name(),
            self.get_pk_value(), other.get_pk_value(),
        ])
        if matches_pk:
            return self.get_pk_value() == other.get_pk_value()

        keys = set(list(self.__data__.keys()) + list(other.__data__.keys()))

        return all(
            [self.__data__.get(key) == other.__data__.get(key)
             for key in keys if key != self.get_pk_name()])

    @classmethod
    def get_pk_name(cls):
        for name, col in cls.table.c.items():
            if col.primary_key:
                return name

    def get_pk_value(cls):
        return getattr(cls, cls.get_pk_name())

    @classmethod
    def get_pk_col(cls, name):
        return getattr(cls.table.c, name)
