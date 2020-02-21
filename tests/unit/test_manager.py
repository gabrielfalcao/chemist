# -*- coding: utf-8 -*-

import sqlalchemy as db
from mock import patch, call, Mock
from datetime import datetime
from chemist import (
    Model,
    Manager,
    InvalidColumnName,
    InvalidQueryModifier,
)

metadata = db.MetaData()


def now():
    return datetime(2012, 12, 12)


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


def test_manager_find_one_by():
    ("Manager#find_one_by finds one record based on the keyword-arguments.")

    class MyTestManager(TestManager):
        query_by = Mock()
        from_result_proxy = Mock(return_value="the results")

    manager = MyTestManager()

    proxy_mock = manager.query_by.return_value
    proxy_mock.fetchone.return_value = "one record"

    # When Manager#find_one_by is called
    result = manager.find_one_by(keyword_one="first", keyword_two="second")

    # Then Manager#query_by is called with the same keyword arguments
    manager.query_by.assert_called_once_with(
        keyword_one="first", keyword_two="second")

    # And Manager#from_result_proxy is called
    manager.from_result_proxy.assert_called_once_with(proxy_mock, "one record")

    # And the `fetchone` method of the proxy is called
    proxy_mock.fetchone.assert_called_once_with()

    # And the result is equal to the result of `from_result_proxy`
    result.should.equal("the results")


@patch('chemist.managers.partial')
def test_manager_find_by(partial):
    ("Manager#find_one_by finds all records matching the keyword arguments.")

    class MyTestManager(TestManager):
        query_by = Mock()
        from_result_proxy = Mock(return_value="the results")

    manager = MyTestManager()

    proxy_mock = manager.query_by.return_value
    proxy_mock.fetchall.return_value = ["one record", "two record", "three record"]

    Models_mock = partial.return_value
    Models_mock.side_effect = lambda x: x

    # When Manager#find_by is called
    result = manager.find_by(keyword_one="first", keyword_two="second")

    # Then Manager#query_by is called with the same keyword arguments
    manager.query_by.assert_called_once_with(
        keyword_one="first", keyword_two="second")

    # And a partial function is formed from the `from_result_proxy` method
    # of Manager and the proxy
    partial.assert_called_once_with(manager.from_result_proxy, proxy_mock)

    # And the `fetchall` method of the proxy is called
    proxy_mock.fetchall.assert_called_once_with()

    # And the result of the partial function is called on the rest of the results
    Models_mock.assert_has_calls([
        call("one record"),
        call("two record"),
        call("three record")
    ])

    # And the result is equal to the result of `from_result_proxy`
    result.should.equal(["one record", "two record", "three record"])


def test_manager_all():

    class MyTestManager(TestManager):
        find_by = Mock(return_value="the result")

    manager = MyTestManager()

    manager.all().should.equal("the result")
    manager.find_by.assert_called_once_with(limit_by=None, offset_by=None, order_by=None)


def test_manager_all_with_limit():

    class MyTestManager(TestManager):
        find_by = Mock(return_value="the result")

    manager = MyTestManager()

    manager.all(limit_by=100).should.equal("the result")
    manager.find_by.assert_called_once_with(limit_by=100, offset_by=None, order_by=None)


def test_manager_all_with_offset():

    class MyTestManager(TestManager):
        find_by = Mock(return_value="the result")

    manager = MyTestManager()

    manager.all(offset_by=100, limit_by=20).should.equal("the result")
    manager.find_by.assert_called_once_with(limit_by=20, offset_by=100, order_by=None)


def test_manager_all_with_order_by():
    class MyTestManager(TestManager):
        find_by = Mock(return_value="the result")

    manager = MyTestManager()

    manager.all(offset_by=100, limit_by=20, order_by='some_field').should.equal("the result")
    manager.find_by.assert_called_once_with(limit_by=20, offset_by=100, order_by='some_field')


def test_manager_get_connection():
    ("Manager#get_connection should call the connect method of the instance's "
     "engine attribute")

    class MyTestManager(TestManager):

        engine = Mock(connect=Mock(return_value="fake connect"))

    # Given a Manager instance whose engine.connect returns a connection
    manager = MyTestManager()

    # When `get_connection` is called
    connection = manager.get_connection()

    # Then `engine.connect` is called
    manager.engine.connect.assert_called_once_with()

    # And the result should equal the result of `engine.connect`
    connection.should.equal("fake connect")


def test_manager_from_result_proxy_without_result():
    "Manager#from_result_proxy without result returns None"

    proxy = Mock()
    proxy.keys.return_value = ['name', 'id', 'age']
    manager = TestManager()
    manager.from_result_proxy(proxy, {}).should.be.none


def test_from_result_proxy_with_result():
    "Manager#from_result_proxy with result"

    proxy = Mock()
    proxy.keys.return_value = ['name', 'id', 'age']

    engine_mock = Mock()
    model = DummyUserModel

    manager = Manager(model, engine_mock)
    manager.from_result_proxy(proxy, ('Foobar', 1, 33)).should.be.a(DummyUserModel)


def test_manager_create():
    "Manager#create should create an instance and save it in the database"

    instance_mock = Mock()

    model_mock = Mock(return_value=instance_mock)
    engine_mock = Mock()

    class MyCreatableManager(TestManager):

        model = model_mock
        engine = engine_mock

    manager = MyCreatableManager()

    d = manager.create(id=1, name='foobar')
    model_mock.assert_called_once_with(engine=engine_mock, id=1, name='foobar')

    d.should.equal(instance_mock.save.return_value)
    instance_mock.save.assert_called_once_with()


def test_manager_get_or_create_when_exists():
    ("Manager#get_or_create should return an existing instance if "
     "it was found in the database")

    find_one_by_mock = Mock()

    class MyFindableManager(TestManager):

        find_one_by = find_one_by_mock

    manager = MyFindableManager()

    d = manager.get_or_create(id=1, name='foobar')
    d.should.equal(find_one_by_mock.return_value)


def test_manager_get_or_create_when_does_not_exist():
    ("Manager#get_or_create should create a new instance if "
     "it was not found in the database")

    find_one_by_mock = Mock()
    find_one_by_mock.return_value = None

    create_mock = Mock()
    create_mock.return_value = None

    class MyFCreatableManager(TestManager):

        find_one_by = find_one_by_mock
        create = create_mock

    manager = MyFCreatableManager()

    d = manager.get_or_create(id=1, name='foobar')
    d.should.equal(create_mock.return_value)


def test_getattribute_from_model():
    ("Managers should allow getting their column values as instance attributes")

    # Given a DB connection
    connection_mock = Mock()

    # And its result proxy
    result = connection_mock.execute.return_value

    class MyDummyUserModel(DummyUserModel):
        pass

    class MyDummyUserManager(TestManager):
        model = MyDummyUserModel
        get_connection = Mock()
        engine = Mock(connect=Mock(return_value=connection_mock))

    manager = MyDummyUserManager()

    # And that the result id is 333
    result.inserted_primary_key = [333]

    # And the last inserted params of the result is an empty dict
    # TODO: better explanation?
    result.last_inserted_params.return_value = {}

    data = {
        "name": "Gabriel",
        "age": '25',
    }
    created = manager.create(**data)

    created.should.have.property('id').being.equal(333)
    created.should.have.property('name').being.equal("Gabriel")
    created.should.have.property('age').being.equal(25)


def test_getattribute_from_model_with_falsy_value():
    ("Managers that were given an empty value are left as they are")

    # Given a DB connection
    connection_mock = Mock()

    class MyDummyUserModel(DummyUserModel):
        pass

    class MyDummyUserManager(TestManager):
        model = MyDummyUserModel
        get_connection = Mock()
        engine = Mock(connect=Mock(return_value=connection_mock))

    manager = MyDummyUserManager()

    # And its result proxy
    result = connection_mock.execute.return_value

    # And that the result id is 333
    result.inserted_primary_key = [333]

    # And the last inserted params of the result is an empty dict
    # TODO: better explanation?
    result.last_inserted_params.return_value = {}

    data = {
        "name": "Gabriel",
        "age": '',
    }
    created = manager.create(**data)

    created.should.have.property('id').being.equal(333)
    created.should.have.property('name').being.equal("Gabriel")
    created.should.have.property('age').being.equal('')


def test_query_by():
    ("Manager#query_by should take keyword args and "
     "query by them using an AND clause")

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
    result = manager.query_by(name='foo')

    # Then the result should be the result proxy
    result.should.equal(proxy)

    # And the query must be correctly done
    connection_mock.execute.called.should.be.true

    x = connection_mock.execute.call_args[0][0]
    str(x).should.equal(
        'SELECT dummy_user_model.id, dummy_user_model.name, dummy_user_model.age \n'
        'FROM dummy_user_model \n'
        'WHERE dummy_user_model.name = :name_1 '
        'ORDER BY dummy_user_model.id DESC')


def test_query_by_limit_by():
    ("Manager#query_by accept the special case argument `limit_by`")

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
    result = manager.query_by(name='foo', limit_by=100)

    # Then the result should be the result proxy
    result.should.equal(proxy)

    # And the query must be correctly done
    connection_mock.execute.called.should.be.true

    x = connection_mock.execute.call_args[0][0]
    str(x).should.equal(
        'SELECT dummy_user_model.id, dummy_user_model.name, dummy_user_model.age \n'
        'FROM dummy_user_model \n'
        'WHERE dummy_user_model.name = :name_1 '
        'ORDER BY dummy_user_model.id DESC\n '
        'LIMIT :param_1')


def test_query_by_offset_by():
    ("Manager#query_by accept the special case argument `offset_by`")

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
    result = manager.query_by(name='foo', offset_by=100)

    # Then the result should be the result proxy
    result.should.equal(proxy)

    # And the query must be correctly done
    connection_mock.execute.called.should.be.true

    x = connection_mock.execute.call_args[0][0]
    str(x).should.equal(
        'SELECT dummy_user_model.id, dummy_user_model.name, dummy_user_model.age '
        '\nFROM dummy_user_model \nWHERE dummy_user_model.name = :name_1 ORDER '
        'BY dummy_user_model.id DESC\n LIMIT -1 OFFSET :param_1')


def test_query_by_startswith():
    ("Manager#query_by should allow the 'startswith' query modifier")
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
    result = manager.query_by(name__startswith='foo')

    # Then the result should be the result proxy
    result.should.equal(proxy)

    # And the query must be correctly done
    connection_mock.execute.called.should.be.true

    # And the SQL should be correct
    x = connection_mock.execute.call_args[0][0]
    str(x).should.equal(
        "SELECT dummy_user_model.id, dummy_user_model.name, dummy_user_model.age \nFROM dummy_user_model \nWHERE (dummy_user_model.name LIKE :name_1 || '%') ORDER BY dummy_user_model.id DESC"
    )


def test_query_by_contains():
    ("Manager#query_by should allow the 'contains' query modifier")
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
    result = manager.query_by(name__contains='foo')

    # Then the result should be the result proxy
    result.should.equal(proxy)

    # And the query must be correctly done
    connection_mock.execute.called.should.be.true

    # And the SQL should be correct
    x = connection_mock.execute.call_args[0][0]
    str(x).should.equal(
        "SELECT dummy_user_model.id, dummy_user_model.name, "
        "dummy_user_model.age \nFROM dummy_user_model \nWHERE "
        "(dummy_user_model.name LIKE '%' || :name_1 || '%' ESCAPE '#') "
        "ORDER BY dummy_user_model.id DESC"
    )


def test_query_by_invalid_column():
    ("Calling Manager#query_by with an invalid field should cause an "
     "exception")

    # Given a DB connection
    connection_mock = Mock()

    # And a model and its manager
    class MyDummyUserModel(DummyUserModel):
        pass

    class MyDummyUserManager(TestManager):
        model = MyDummyUserModel
        get_connection = Mock(return_value=connection_mock)

    manager = MyDummyUserManager()

    # If we query for an invalid field
    manager.query_by.when.called_with(
        invalid_field="some value",
    ).should.throw(
        InvalidColumnName
    )


def test_query_by_invalid_query_modifier():
    ("Calling Manager#query_by with an invalid query modifier should cause an "
     "exception")

    # Given a DB connection
    connection_mock = Mock()

    # And a model and its manager
    class MyDummyUserModel(DummyUserModel):
        pass

    class MyDummyUserManager(TestManager):
        model = MyDummyUserModel
        get_connection = Mock(return_value=connection_mock)

    manager = MyDummyUserManager()

    # If we query with an invalid modifier
    manager.query_by.when.called_with(
        name__somemodifier="some value",
    ).should.throw(
        InvalidQueryModifier
    )


def test_generate_query_by_order_by():
    ("Calling Manager.query_by with an order_by parameter should return the "
     "results in descending order of that field")

    # Given a DB connection
    connection_mock = Mock()

    class MyDummyUserModel(DummyUserModel):
        pass

    class MyDummyUserManager(TestManager):
        model = MyDummyUserModel
        get_connection = Mock(return_value=connection_mock)

    manager = MyDummyUserManager()

    # When I try to generate a query
    result = manager.generate_query(order_by='id')

    # Then the SQL should be correct
    str(result).should.equal(
        'SELECT dummy_user_model.id, dummy_user_model.name, '
        'dummy_user_model.age \nFROM dummy_user_model ORDER BY '
        'dummy_user_model.id DESC'
    )


def test_generate_query_by_order_by_descending():
    ("Calling Manager.query_by with an order_by that starts with '-' will "
     "return results in descending order")

    # Given a DB connection
    connection_mock = Mock()

    class MyDummyUserModel(DummyUserModel):
        pass

    class MyDummyUserManager(TestManager):
        model = MyDummyUserModel
        get_connection = Mock(return_value=connection_mock)

    manager = MyDummyUserManager()

    # When I try to generate a query
    result = manager.generate_query(order_by='-id')

    # Then the SQL should be correct
    str(result).should.equal(
        'SELECT dummy_user_model.id, dummy_user_model.name, '
        'dummy_user_model.age \nFROM dummy_user_model ORDER BY '
        'dummy_user_model.id DESC'
    )


def test_generate_query_by_order_by_ascending():
    ("Calling Manager.query_by with an order_by that starts with '+' will "
     "return results in ascending order")

    # Given a DB connection
    connection_mock = Mock()

    class MyDummyUserModel(DummyUserModel):
        pass

    class MyDummyUserManager(TestManager):
        model = MyDummyUserModel
        get_connection = Mock(return_value=connection_mock)

    manager = MyDummyUserManager()

    # When I try to generate a query
    result = manager.generate_query(order_by='+id')

    # Then the SQL should be correct
    str(result).should.equal(
        'SELECT dummy_user_model.id, dummy_user_model.name, '
        'dummy_user_model.age \nFROM dummy_user_model ORDER BY '
        'dummy_user_model.id ASC'
    )


@patch('chemist.managers.Manager.from_result_proxy')
def test_many_from_result_proxy(from_result_proxy):
    "Manager#many_from_result_proxy should call "
    "from_result_proxy on each item found in proxy.fetchall()"

    from_result_proxy.side_effect = ['bound1', 'bound2']
    proxy = Mock()
    proxy.fetchall.return_value = ['item1', 'item2']

    engine_mock = Mock()
    model = DummyUserModel

    manager = Manager(model, engine_mock)
    result = manager.many_from_result_proxy(proxy)

    from_result_proxy.assert_has_calls([
        call(proxy, 'item1'),
        call(proxy, 'item2'),
    ])

    result.should.equal(['bound1', 'bound2'])


@patch('chemist.managers.Manager.get_connection')
@patch('chemist.managers.Manager.many_from_result_proxy')
def test_many_from_query(
        many_from_result_proxy, get_connection):
    ("Manager#many_from_query should execute the given "
     "query and return many results from it")

    connection = get_connection.return_value
    proxy = connection.execute.return_value

    engine_mock = Mock()
    model = DummyUserModel

    manager = Manager(model, engine_mock)
    result = manager.many_from_query("the query")
    result.should.equal(many_from_result_proxy.return_value)

    connection.execute.assert_called_once_with('the query')
    get_connection.assert_called_once_with()
    many_from_result_proxy.assert_called_once_with(proxy)


@patch('chemist.managers.Manager.get_connection')
@patch('chemist.managers.Manager.from_result_proxy')
def test_one_from_query(
        from_result_proxy, get_connection):
    ("Manager#one_from_query should execute the given "
     "query and return the result")

    connection = get_connection.return_value
    proxy = connection.execute.return_value

    engine_mock = Mock()
    model = DummyUserModel

    manager = Manager(model, engine_mock)
    result = manager.many_from_result_proxy(proxy)

    result = manager.one_from_query("the query")
    result.should.equal(from_result_proxy.return_value)
    from_result_proxy.assert_called_once_with(
        proxy,
        proxy.fetchone.return_value,
    )
