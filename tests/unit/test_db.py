#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sqlalchemy as db
from mock import patch, Mock
from datetime import datetime
from decimal import Decimal
from chemist import (
    Model,
    Manager,
    InvalidModelDeclaration,
    InvalidColumnName,
    EngineNotSpecified,
    MultipleEnginesSpecified,
)

metadata = db.MetaData()


def now():
    return datetime(2012, 12, 12)


def table_mock(name, **columns):
    mock = Mock(name=name)
    mock.columns = columns
    return mock


class DummyUserModel(Model):
    table = db.Table('dummy_user_model', metadata,
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('name', db.String(80)),
                     db.Column('age', db.Integer))


class ExquisiteModel(Model):
    table = db.Table('dummy_exquisite', metadata,
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('score', db.Numeric(), default='10.3'),
                     db.Column('created_at', db.DateTime(), default=now))


class TestManager(Manager):
    def __init__(self):
        pass


class ModelEngineTestManager(Manager):

    def __init__(self):
        self.model = Mock()
        self.engine = Mock()


class ModelInputTestManager(Manager):

    def __init__(self, model):
        self.model = model
        self.engine = Mock()


def test_instantiating_model_with_preprocessed_data():
    ("Instantiating a model with preprocessed data")

    class UserTwiceAsOld(Model):
        table = db.Table('twice_as_old_user', metadata,
                         db.Column('id', db.Integer, primary_key=True),
                         db.Column('name', db.String(80)),
                         db.Column('age', db.Integer))

        def preprocess(self, data):
            data['age'] = int(data.get('age', 0)) * 2
            return data

    old_user = UserTwiceAsOld(name='Chuck Norris', age=33)
    old_user.age.should.equal(66)
    old_user.name.should.equal('Chuck Norris')


def test_preprocess_should_return_dict():
    ("Model.preprocess should always return a dict")

    class AnotherUserModel(Model):
        table = db.Table('another_user_model', metadata,
                         db.Column('id', db.Integer, primary_key=True),
                         db.Column('name', db.String(80)),
                         db.Column('age', db.Integer))

        def preprocess(self, data):
            data['age'] = int(data.get('age', 0)) * 2

    AnotherUserModel.when.called_with(name='Chuck Norris', age=33).should.throw(
        InvalidModelDeclaration, 'The model `AnotherUserModel` declares a preprocess method but it does not return a dictionary!')


def test_creating_model_with_invalid_keyword_arguments():
    ("Instantiating a model with invalid fields as keyword "
     "arguments should raise an exception")

    DummyUserModel.when.called_with(inexistent_field='foobar').should.throw(
        InvalidColumnName, "inexistent_field is not a valid column name for the model "
        "tests.unit.test_db.DummyUserModel (['age', 'id', 'name'])")


def test_model_represented_as_string():
    ("A Model should have a string representation")

    u = DummyUserModel(id=1, name='Gabriel', age=25)
    repr(u).should.equal('<DummyUserModel id=1>')


def test_model_to_dict():
    "Model.to_dict should return prepare the model data to be serialized"


    j = ExquisiteModel(score=Decimal('2.3'), created_at=datetime(2010, 10, 10))

    j.to_dict().should.equal({'score': '2.30', 'created_at': '2010-10-10T00:00:00', 'id': None})


def test_model_to_insert_params():
    ("Model.to_insert_params should return the result of "
     "to_dict() minus the keys that are not valid table field names")

    class MyModel(ExquisiteModel):
        def to_dict(self):
            data = super(MyModel, self).to_dict()
            data['FOOBAR'] = {'whaaat': 'yes!'}
            return data

    j = MyModel(score=Decimal('2.3'), created_at=datetime(2010, 10, 10))

    j.to_insert_params().should.equal({'score': '2.30', 'created_at': '2010-10-10T00:00:00'})


def test_model_serialize_value_decimal():
    "Model.serialize_value should serialize decimals whatsoever"

    j = ExquisiteModel()

    j.serialize_value('score', Decimal('10.3')).should.equal('10.30')


def test_model_serialize_value_datetime():
    "Model.serialize_value should serialize datetime objects whatsoever"

    j = ExquisiteModel()

    j.serialize_value('created_at', datetime(2010, 10, 10)).should.equal('2010-10-10T00:00:00')


def test_model_serialize_value_callable():
    ("Model.serialize_value should try to use the default if the "
     "given value is falsy and default value is callable")

    j = ExquisiteModel()

    j.serialize_value('created_at', '').should.equal('2012-12-12T00:00:00')
    j.serialize_value('created_at', False).should.equal('2012-12-12T00:00:00')
    j.serialize_value('created_at', None).should.equal('2012-12-12T00:00:00')


def test_model_serialize_value_not_callable():
    ("Model.serialize_value should try to use the default if the "
     "given value is falsy and default value is NOT callable")

    j = ExquisiteModel()

    j.serialize_value('score', '').should.equal(Decimal('10.3'))
    j.serialize_value('score', False).should.equal(Decimal('10.3'))
    j.serialize_value('score', None).should.equal(Decimal('10.3'))


def test_model_deserialize_value():
    "Model.deserialize_value should parse datetime values"

    # Given a model that has a DateTime field
    class DatetimeSensitiveModel(Model):
        table = db.Table('datetime_sensitive_model', metadata,
                         db.Column('id', db.Integer, primary_key=True),
                         db.Column('a_date_field', db.DateTime()))

    # And an instance of that model
    j = DatetimeSensitiveModel()

    # When I deserialize a value for that field
    value = j.deserialize_value('a_date_field', '2010-10-10T00:00:00')

    # Then it should be a real datetime
    value.should.be.a(datetime)
    value.year.should.equal(2010)
    value.month.should.equal(10)
    value.day.should.equal(10)


def test_model_to_json():
    "Model.to_json should return serialized model data"

    j = DummyUserModel(name='Jeez', age=33)

    j.to_json().should.equal('{"age": 33, "id": null, "name": "Jeez"}')


def test_model_getattr():
    "Model data should be possible to be retrieved through __getattr__"

    j = DummyUserModel(name='Jeez', age=33)

    j.should.have.property('name').being.equal('Jeez')
    j.should.have.property('__data__').being.equal({'age': 33, 'name': 'Jeez'})


def test_model_get():
    "Model data can be accessed by get"

    instance = DummyUserModel(name='Jeez')

    instance.get('name').should.equal('Jeez')
    instance.get('age').should.be.none
    instance.get('age', 123).should.equal(123)


def test_model_set():
    ("Model#set can set many keyword arguments at "
     "once for a sinle model instance")

    instance = DummyUserModel(name='Dummy One', age=20)
    instance.save = Mock()
    instance.set(
        name="Another Two",
        age=40,
    )

    instance.name.should.equal("Another Two")
    instance.age.should.equal(40)

    instance.save.called.should.be.false


def test_model_set_invalid_col():
    ("Model#set raises InvalidColumnName if an invalid "
     "name is given")

    instance = DummyUserModel(id=33, name='Dummy One', age=20)

    instance.set.when.called_with(
        name="Another Two",
        age=40,
        foo="bar"
    ).should.throw(
        InvalidColumnName,
        "<DummyUserModel id=33>.foo",
    )


@patch.object(DummyUserModel, 'find_one_by')
def test_model_refresh(find_one_by):
    ("Model#refresh should find the newest data and "
     "update itself with that data")

    find_one_by.return_value.__data__ = {'name': "NEW TWO"}
    instance = DummyUserModel(id=44, name='Dummy One', age=20)
    instance.refresh()

    find_one_by.assert_called_once_with(
        id=44
    )

    instance.name.should.equal("NEW TWO")


def test_model_equality():
    "Model equality is based off ID if each has an ID."

    instance = DummyUserModel(id=1, name='Jeez')
    other_instance = DummyUserModel(id=1, name='NotJeez')

    third_instance = DummyUserModel(id=2, name='Jeez')

    instance.should.equal(other_instance)
    instance.should_not.equal(third_instance)


def test_model_equality_no_id():
    "Model equality is based off data if either does not have an ID."

    instance = DummyUserModel(name='Jeez')
    other_instance = DummyUserModel(name='NotJeez')

    third_instance = DummyUserModel(name='Jeez')

    instance.should_not.equal(other_instance)
    instance.should.equal(third_instance)


def test_model_get_engine_inputted_engine():
    ("Getting the engine for a Model should return the `engine` attribute if "
     "it is not None and the inputted engine IS None. Also, it should "
     "return the inputted engine if it is not None and the `engine` attribute "
     "IS None. Otherwise, throw errors.")

    # Given a model instance with no engine specified
    instance = DummyUserModel()

    # When calling get_engine on it with a non-None engine as input
    engine = instance.get_engine("an engine inputted")

    # Then the result is the inputted engine
    engine.should.equal("an engine inputted")


def test_model_get_engine_multiple_engines():
    ("Getting the engine for a Model should return the `engine` attribute if "
     "it is not None and the inputted engine IS None. Also, it should "
     "return the inputted engine if it is not None and the `engine` attribute "
     "IS None. Otherwise, throw errors.")

    # Given a model instance with an engine specified
    instance = DummyUserModel(engine="init engine")

    # When calling get_engine on it with a non-None engine as input
    # Then it should throw a MultipleEnginesSpecified Exception
    instance.get_engine.when.called_with("an engine inputted").should.throw(
        MultipleEnginesSpecified)


def test_model_get_engine_initialized_engine():
    ("Getting the engine for a Model should return the `engine` attribute if "
     "it is not None and the inputted engine IS None. Also, it should "
     "return the inputted engine if it is not None and the `engine` attribute "
     "IS None. Otherwise, throw errors.")

    # Given a model instance with an engine specified
    instance = DummyUserModel(engine="init engine")

    # When calling get_engine with no input
    engine = instance.get_engine()

    # Then the result is the initial engine
    engine.should.equal("init engine")


def test_model_get_engine_no_engines():
    ("Getting the engine for a Model should return the `engine` attribute if "
     "it is not None and the inputted engine IS None. Also, it should "
     "return the inputted engine if it is not None and the `engine` attribute "
     "IS None. Otherwise, throw errors.")

    # Given a model instance with no engine specified
    instance = DummyUserModel()

    # When calling get_engine with no input
    # Then it should throw a EngineNotSpecified Exception
    instance.get_engine.when.called_with().should.throw(
        EngineNotSpecified)


def test_model_using():

    class MyDummyUserModel(DummyUserModel):

        manager = Mock()

    engine_mock = Mock(name='engine')
    MyDummyUserModel.using(engine_mock)

    MyDummyUserModel.manager.assert_called_once_with(
        MyDummyUserModel, engine_mock)


def test_model_is_persisted_true():
    ("Model#is_persisted evaluates to True if the Model instance "
     "has an id field.")

    instance = DummyUserModel(id=123)
    instance.is_persisted.should.be.true


def test_model_is_persisted_false():
    ("Model#is_persisted evaluates to False if the Model instance "
     "does NOT have an id field.")

    instance = DummyUserModel()
    instance.is_persisted.should.be.false


class MySaveableModel(Model):
    table = db.Table('my_saveable_model', metadata,
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('name', db.String(80)),
    )

    get_engine = Mock()


def test_model_save_new():
    "Saving a new model from the database uses its id"

    d = MySaveableModel(name='foobar')

    engine_mock = d.get_engine.return_value

    db_mock = engine_mock.connect.return_value

    result = db_mock.execute.return_value

    # And the last inserted params of the result is an empty dict
    # TODO: better explanation?
    result.last_inserted_params.return_value = {}

    # And that the result id is 333
    result.inserted_primary_key = [333]

    d.save().should.equal(d)

    db_mock.execute.call_args.should.have.length_of(2)
    query = db_mock.execute.call_args[0][0]
    str(query).should.equal(
        'INSERT INTO my_saveable_model (name) VALUES (:name)')


def test_model_save_existing():
    "Saving an existing model from the database uses its id"

    d = MySaveableModel(id=1, name='foobar')

    engine_mock = d.get_engine.return_value

    db_mock = engine_mock.connect.return_value

    result = db_mock.execute.return_value

    # And that the result id is 333
    result.inserted_primary_key = [333]

    # And the last inserted params of the result is an empty dict
    # TODO: better explanation?
    result.last_updated_params.return_value = {}

    d.save().should.equal(d)

    db_mock.execute.call_args.should.have.length_of(2)
    query = db_mock.execute.call_args[0][0]
    str(query).should.equal(
        'UPDATE my_saveable_model SET name=:name WHERE my_saveable_model.id = :id_1')


class MyDeletableModel(Model):
    table = db.Table('my_deletable_model', metadata,
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('name', db.String(80)),
    )

    get_engine = Mock()


def test_model_delete():
    "Deleting a model from the database uses its id"

    d = MyDeletableModel(id=1, name='foobar')

    db_mock = d.get_engine.return_value.connect.return_value
    d.delete().should.equal(db_mock.execute.return_value)

    db_mock.execute.call_args.should.have.length_of(2)
    query = db_mock.execute.call_args[0][0]
    str(query).should.equal(
        'DELETE FROM my_deletable_model WHERE my_deletable_model.id = :id_1')


def test_model_create_calls_manager_with_default_engine():
    ("Model.create() should be a proxy to Model#using(engine).create()")

    # Given a subclass of Model that mocks the class method: using()
    class ManagedModel(Model):
        using = Mock(name='ManagedModel.using')
        table = table_mock('ManagedModel')

    # When I call create
    result = ManagedModel.create(one=1, two=2)

    # Then the result must have come from the mock
    result.should.equal(ManagedModel.using.return_value.create.return_value)

    # And it should have been called appropriately
    ManagedModel.using.return_value.create.assert_called_once_with(one=1, two=2)

    # And it should have been called appropriately
    ManagedModel.using.assert_called_once_with(None)


def test_model_get_or_create_calls_manager_with_default_engine():
    ("Model.get_or_create() should be a proxy to Model#using(engine).get_or_create()")

    # Given a subclass of Model that mocks the class method: using()
    class ManagedModel(Model):
        using = Mock(name='ManagedModel.using')
        table = table_mock('ManagedModel')

    # When I call get_or_create
    result = ManagedModel.get_or_create(one=1, two=2)

    # Then the result must have come from the mock
    result.should.equal(ManagedModel.using.return_value.get_or_create.return_value)

    # And it should have been called appropriately
    ManagedModel.using.return_value.get_or_create.assert_called_once_with(one=1, two=2)

    # And it should have been called appropriately
    ManagedModel.using.assert_called_once_with(None)


def test_model_query_by_calls_manager_with_default_engine():
    ("Model.query_by() should be a proxy to Model#using(engine).query_by()")

    # Given a subclass of Model that mocks the class method: using()
    class ManagedModel(Model):
        using = Mock(name='ManagedModel.using')
        table = table_mock('ManagedModel')

    # When I call query_by
    result = ManagedModel.query_by(order_by='ORDERING', one=1, two=2)

    # Then the result must have come from the mock
    result.should.equal(ManagedModel.using.return_value.query_by.return_value)

    # And it should have been called appropriately
    ManagedModel.using.return_value.query_by.assert_called_once_with(
        order_by='ORDERING', one=1, two=2)

    # And it should have been called appropriately
    ManagedModel.using.assert_called_once_with(None)


def test_model_find_one_by_calls_manager_with_default_engine():
    ("Model.find_one_by() should be a proxy to Model#using(engine).find_one_by()")

    # Given a subclass of Model that mocks the class method: using()
    class ManagedModel(Model):
        using = Mock(name='ManagedModel.using')
        table = table_mock('ManagedModel')

    # When I call find_one_by
    result = ManagedModel.find_one_by(one=1, two=2)

    # Then the result must have come from the mock
    result.should.equal(ManagedModel.using.return_value.find_one_by.return_value)

    # And it should have been called appropriately
    ManagedModel.using.return_value.find_one_by.assert_called_once_with(one=1, two=2)

    # And it should have been called appropriately
    ManagedModel.using.assert_called_once_with(None)


def test_model_find_by_calls_manager_with_default_engine():
    ("Model.find_by() should be a proxy to Model#using(engine).find_by()")

    # Given a subclass of Model that mocks the class method: using()
    class ManagedModel(Model):
        using = Mock(name='ManagedModel.using')
        table = table_mock('ManagedModel')

    # When I call find_by
    result = ManagedModel.find_by(one=1, two=2)

    # Then the result must have come from the mock
    result.should.equal(ManagedModel.using.return_value.find_by.return_value)

    # And it should have been called appropriately
    ManagedModel.using.return_value.find_by.assert_called_once_with(one=1, two=2)

    # And it should have been called appropriately
    ManagedModel.using.assert_called_once_with(None)


def test_model_all_calls_manager_with_default_engine():
    ("Model.all() should be a proxy to Model#using(engine).all()")

    # Given a subclass of Model that mocks the class method: using()
    class ManagedModel(Model):
        using = Mock(name='ManagedModel.using')
        table = table_mock('ManagedModel')

    # When I call all
    result = ManagedModel.all()

    # Then the result must have come from the mock
    result.should.equal(ManagedModel.using.return_value.all.return_value)

    # And it should have been called appropriately
    ManagedModel.using.return_value.all.assert_called_once_with()

    # And it should have been called appropriately
    ManagedModel.using.assert_called_once_with(None)


def test_total_rows_with_where():
    ("Manager#total_rows should support giving the where clause kwargs")

    # Given a DB connection
    connection_mock = Mock()

    class MyDummyUserModel(DummyUserModel):
        pass

    class MyDummyUserManager(TestManager):
        model = MyDummyUserModel
        get_connection = Mock(return_value=connection_mock)

    manager = MyDummyUserManager()

    # And its result proxy
    proxy = connection_mock.execute.return_value

    # When I try to query a manager by some field
    result = manager.total_rows(age=26, unexisting_field=123)

    # Then the result should be the result proxy
    result.should.equal(proxy.scalar.return_value)

    # And the query must be correctly done
    connection_mock.execute.called.should.be.true

    x = connection_mock.execute.call_args[0][0]
    str(x).should.equal(
        'SELECT count(dummy_user_model.id) AS tbl_row_count '
        '\nFROM dummy_user_model \nWHERE dummy_user_model.age = :age_1')


def test_total_rows():
    ("Manager#total_rows should return the count")

    # Given a DB connection
    connection_mock = Mock()

    class MyDummyUserModel(DummyUserModel):
        pass

    class MyDummyUserManager(TestManager):
        model = MyDummyUserModel
        get_connection = Mock(return_value=connection_mock)

    manager = MyDummyUserManager()

    # And its result proxy
    proxy = connection_mock.execute.return_value

    # When I try to query a manager by some field
    result = manager.total_rows()

    # Then the result should be the result proxy
    result.should.equal(proxy.scalar.return_value)

    # And the query must be correctly done
    connection_mock.execute.called.should.be.true

    x = connection_mock.execute.call_args[0][0]
    str(x).should.equal(
        'SELECT count(dummy_user_model.id) AS '
        'tbl_row_count \nFROM dummy_user_model')


def test_model_total_rows_calls_manager_with_default_engine():
    ("Model.total_rows() should be a proxy to Model#using(engine).total_rows()")

    # Given a subclass of Model that mocks the class method: using()
    class ManagedModel(Model):
        using = Mock(name='ManagedModel.using')
        table = table_mock('ManagedModel')

    # When I call total_rows
    result = ManagedModel.total_rows(field_name='name')

    # Then the result must have come from the mock
    result.should.equal(ManagedModel.using.return_value.total_rows.return_value)

    # And it should have been called appropriately
    ManagedModel.using.return_value.total_rows.assert_called_once_with(field_name='name')

    # And it should have been called appropriately
    ManagedModel.using.assert_called_once_with(None)


def test_model_get_connection_calls_manager_with_default_engine():
    ("Model.get_connection() should be a proxy to Model#using(engine).get_connection()")

    # Given a subclass of Model that mocks the class method: using()
    class ManagedModel(Model):
        using = Mock(name='ManagedModel.using')
        table = table_mock('ManagedModel')

    # When I call all
    result = ManagedModel.get_connection()

    # Then the result must have come from the mock
    result.should.equal(ManagedModel.using.return_value.get_connection.return_value)

    # And it should have been called appropriately
    ManagedModel.using.return_value.get_connection.assert_called_once_with()

    # And it should have been called appropriately
    ManagedModel.using.assert_called_once_with(None)


def test_model_many_from_query_calls_manager_with_default_engine():
    ("Model.many_from_query() should be a proxy to Model#using(engine).many_from_query()")

    # Given a subclass of Model that mocks the class method: using()
    class ManagedModel(Model):
        using = Mock(name='ManagedModel.using')
        table = table_mock('ManagedModel')

    # When I call all
    result = ManagedModel.many_from_query("the query")

    # Then the result must have come from the mock
    result.should.equal(ManagedModel.using.return_value.many_from_query.return_value)

    # And it should have been called appropriately
    ManagedModel.using.return_value.many_from_query.assert_called_once_with("the query")

    # And it should have been called appropriately
    ManagedModel.using.assert_called_once_with(None)


def test_model_one_from_query_calls_manager_with_default_engine():
    ("Model.one_from_query() should be a proxy to Model#using(engine).one_from_query()")

    # Given a subclass of Model that mocks the class method: using()
    class ManagedModel(Model):
        using = Mock(name='ManagedModel.using')
        table = table_mock('ManagedModel')

    # When I call all
    result = ManagedModel.one_from_query("the query")

    # Then the result must have come from the mock
    result.should.equal(ManagedModel.using.return_value.one_from_query.return_value)

    # And it should have been called appropriately
    ManagedModel.using.return_value.one_from_query.assert_called_once_with("the query")

    # And it should have been called appropriately
    ManagedModel.using.assert_called_once_with(None)
