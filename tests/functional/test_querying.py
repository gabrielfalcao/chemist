# -*- coding: utf-8 -*-
from sure import scenario
from mock import Mock
from datetime import datetime
from decimal import Decimal
from chemist import (
    Model, db, MetaData,
    set_engine,
    InvalidModelDeclaration,
    InvalidColumnName,
    EngineNotSpecified,
    InvalidQueryModifier,
    MultipleEnginesSpecified,
)

metadata = MetaData()


def reset_db(context):
    engine = set_engine('mysql://root@localhost/chemist')
    metadata.drop_all(engine)
    metadata.create_all(engine)


clean_db = scenario(reset_db, reset_db)


class User(Model):
    table = db.Table('md_user', metadata,
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('github_id', db.Integer, nullable=False, unique=True),
                     db.Column('github_token', db.String(256), nullable=True),
                     db.Column('gravatar_id', db.String(40), nullable=False, unique=True),
                     db.Column('username', db.String(80), nullable=False, unique=True),
                     db.Column('email', db.String(100), nullable=False, unique=True),
                     db.Column('created_at', db.DateTime, default=datetime.now),
                     db.Column('updated_at', db.DateTime, default=datetime.now))


class DummyUserModel(Model):
    table = db.Table('dummy_user_model', metadata,
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('name', db.String(80)),
                     db.Column('age', db.Integer))


def now():
    return datetime(2012, 12, 12)


class ExquisiteModel(Model):
    table = db.Table('dummy_exquisite', metadata,
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('score', db.Numeric(), default='10.3'),
                     db.Column('created_at', db.DateTime(), default=now))


@clean_db
def test_user_signup(context):
    ("User.create(dict) should create a "
     "user in the database")
    data = {
        "username": "octocat",
        "gravatar_id": "somehexcode",
        "email": "octocat@github.com",
        "github_token": 'toktok',
        "github_id": '123',
    }
    created = User.create(**data)
    created.username = 'foo'
    created.save()

    created.should.have.property('id').being.equal(1)
    created.should.have.property('username').being.equal("foo")
    created.should.have.property('github_id').being.equal(123)
    created.should.have.property('github_token').being.equal('toktok')
    created.should.have.property('gravatar_id').being.equal('somehexcode')
    created.should.have.property('email').being.equal('octocat@github.com')


@clean_db
def test_user_all(context):
    ("User.all() should return all existing users")
    data = {
        "username": "octocat",
        "gravatar_id": "somehexcode",
        "email": "octocat@github.com",
        "github_token": 'toktok',
        "github_id": '123',
    }
    created = User.create(**data)

    User.all().should.contain(created)


def test_creating_model_with_invalid_keyword_arguments():
    ("Instantiating a model with invalid fields as keyword "
     "arguments should raise an exception")

    DummyUserModel.when.called_with(inexistent_field='foobar').should.throw(
        InvalidColumnName, "inexistent_field is not a valid column name for the model "
        "tests.functional.test_querying.DummyUserModel (['age', 'id', 'name'])")


def test_model_represented_as_string():
    ("A Model should have a string representation")

    u = DummyUserModel(id=1, name='Gabriel', age=25)
    repr(u).should.equal('<DummyUserModel id=1>')


def test_model_to_dict():
    "Model.to_dict should return prepare the model data to be serialized"

    j = ExquisiteModel(score=Decimal('2.3'), created_at=datetime(2010, 10, 10))

    j.to_dict().should.equal({'score': '2.30', 'created_at': '2010-10-10T00:00:00', 'id': None})


def test_preprocess_should_return_dict():
    ("Model.preprocess should always return a dict")

    class AnotherUserModel(Model):
        table = db.Table('another_user_model', metadata,
                         db.Column('id', db.Integer, primary_key=True),
                         db.Column('name', db.String(80)),
                         db.Column('age', db.Integer),
        )

        def preprocess(self, data):
            data['age'] = int(data.get('age', 0)) * 2

    AnotherUserModel.when.called_with(name='Chuck Norris', age=33).should.throw(
        InvalidModelDeclaration, 'The model `AnotherUserModel` declares a preprocess method but it does not return a dictionary!')


@clean_db
def test_user_signup_get_or_create_if_already_exists(context):
    ("User.get_or_create(dict) should get"
     "user from the database if already exists")

    data = {
        "username": "octocat",
        "gravatar_id": "somehexcode",
        "email": "octocat@github.com",
        "github_token": 'toktok',
        "github_id": '123',
    }
    created = User.create(**data)
    created.is_persisted.should.be.true
    got = User.get_or_create(**data)
    got.is_persisted.should.be.true
    got.should.equal(created)


@clean_db
def test_delete_user(context):
    ("User.delete() should delete from the database")

    data = {
        "username": "octocat",
        "gravatar_id": "somehexcode",
        "email": "octocat@github.com",
        "github_token": 'toktok',
        "github_id": '123',
    }
    created = User.create(**data)
    created.delete()

    got = User.get_or_create(**data)

    got.should_not.equal(created)


@clean_db
def test_save_without_engine(context):
    ("User.save() without engine should raise EngineNotSpecified")
    data = {
        "username": "octocat",
        "gravatar_id": "somehexcode",
        "email": "octocat@github.com",
        "github_token": 'toktok',
        "github_id": '123',
    }

    created = User.create(**data)
    created.engine = None
    created.save.when.called.should.throw(
        EngineNotSpecified,
        "You must specify a SQLAlchemy engine object in order to "
        "do operations in this model instance: <User id=1>"
    )


@clean_db
def test_get_engine_when_already_has_one(context):
    ("User.get_engine() passing an engine when the object "
     "already has one should raise exception")
    data = {
        "username": "octocat",
        "gravatar_id": "somehexcode",
        "email": "octocat@github.com",
        "github_token": 'toktok',
        "github_id": '123',
    }

    created = User.create(**data)

    created.get_engine.when.called_with(True).should.throw(
        MultipleEnginesSpecified,
        "This model instance has a SQLAlchemy engine object already. "
        "You may not save it to another engine."
    )


@clean_db
def test_user_signup_get_or_create_doesnt_exist(context):
    ("User.get_or_create(dict) should get"
     "user from the database if it does not exist yet")

    data = {
        "username": "octocat",
        "gravatar_id": "somehexcode",
        "email": "octocat@github.com",
        "github_token": 'toktok',
        "github_id": '123',
    }
    created = User.create(**data)

    created.should.have.property('id').being.equal(1)
    created.should.have.property('username').being.equal("octocat")
    created.should.have.property('github_id').being.equal(123)
    created.should.have.property('github_token').being.equal('toktok')
    created.should.have.property('gravatar_id').being.equal('somehexcode')
    created.should.have.property('email').being.equal('octocat@github.com')


@clean_db
def test_find_one_by(context):
    ("User.find_one_by(**kwargs) should fetch user from the database")

    data = {
        "username": "octocat",
        "gravatar_id": "somehexcode",
        "email": "octocat@github.com",
        "github_token": 'toktok',
        "github_id": '123',
    }

    original_user = User.create(**data)

    User.find_one_by(id=1).should.be.equal(original_user)
    User.find_one_by(username='octocat').should.be.equal(original_user)


@clean_db
def test_query_modifier_contains(context):
    ("User.find_one_by(**kwargs) should fetch user from the database")

    data = {
        "username": "octocat",
        "gravatar_id": "somehexcode",
        "email": "octocat@github.com",
        "github_token": 'toktok',
        "github_id": '123',
    }

    original_user = User.create(**data)

    User.find_one_by(username__contains='toc').should.be.equal(original_user)
    User.find_one_by(email__contains='@git').should.be.equal(original_user)


@clean_db
def test_find_one_by_not_exists(context):
    ("User.find_one_by(**kwargs) should return None if does not exist")

    User.find_one_by(username='octocat').should.be.none


@clean_db
def test_query_by_not_exists(context):
    ("User.query_by(**kwargs) should return None if does not exist")

    list(User.query_by(username='octocat')).should.be.empty


@clean_db
def test_query_by_invalid_column(context):
    ("User.query_by(**kwargs) should raise an exception if the field does not"
     " exist")

    User.query_by.when.called_with(
        invalidfield="some value",
    ).should.throw(
        InvalidColumnName
    )


@clean_db
def test_query_by_invalid_query_modifier(context):
    ("User.query_by(**kwargs) should raise an exception if the field does not"
     " exist")

    User.query_by.when.called_with(
        email__invalidmodifier="some value",
    ).should.throw(
        InvalidQueryModifier
    )


@clean_db
def test_find_many_by_not_exists(context):
    ("User.find_by(**kwargs) should return an empty list if does not exist")

    User.find_by(username='octocat').should.be.empty


@clean_db
def test_find_by(context):
    ("User.find_by(**kwargs) should fetch a list of users from the database")

    data1 = {
        "username": "octocat",
        "github_id": 42,
        "gravatar_id": "somehexcode2",
        "email": "octocat@github.com",
        "github_token": "toktok",
    }

    data2 = {
        "username": "octopussy",
        "github_id": 88,
        "gravatar_id": "somehexcode1",
        "email": "octopussy@github.com",
        "github_token": "toktok",
    }

    original_user1 = User.create(**data1)
    original_user2 = User.create(**data2)

    User.find_by(github_token='toktok').should.be.equal([
        original_user2,
        original_user1
    ])


@clean_db
def test_find_by_with_limit_by(context):
    ("User.find_by(limit_by=100, **kwargs) should limit the number of users")

    data1 = {
        "username": "octocat",
        "github_id": 42,
        "gravatar_id": "somehexcode2",
        "email": "octocat@github.com",
        "github_token": "toktok",
    }

    data2 = {
        "username": "octopussy",
        "github_id": 88,
        "gravatar_id": "somehexcode1",
        "email": "octopussy@github.com",
        "github_token": "toktok",
    }

    User.create(**data1)
    original_user2 = User.create(**data2)

    User.find_by(github_token='toktok', limit_by=1).should.be.equal([
        original_user2,
    ])


@clean_db
def test_find_by_with_limit_by_and_offset(context):
    ("User.find_by(limit_by=5, offset=3, **kwargs) should limit "
     "to 2 users, offsetting 2 users")

    make_user = lambda x: User.create(**{
        "username": "octocat{0}".format(x),
        "github_id": x,
        "gravatar_id": "somehexcode{0}".format(x),
        "email": "octocat{0}@github.com".format(x),
        "github_token": "toktok{0}".format(x),
    })

    users = list(reversed([make_user(x) for x in range(10)]))

    User.find_by(limit_by=5, offset_by=3).should.be.equal(users[3:8])


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

    j.serialize_value('score', '').should.equal('10.3')
    j.serialize_value('score', False).should.equal('10.3')
    j.serialize_value('score', None).should.equal('10.3')


def test_model_deserialize_value():
    "Model.deserialize_value should parse datetime values"

    # Given a model that has a DateTime field
    class DatetimeSensitiveModel(Model):
        table = db.Table('datetime_sensitive_model', metadata,
                         db.Column('id', db.Integer, primary_key=True),
                         db.Column('a_date_field', db.DateTime()),
        )

    # And an instance of that model
    j = DatetimeSensitiveModel()

    # When I deserialize a value for that field
    value = j.deserialize_value('a_date_field', '2010-10-10 00:00:00')

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
