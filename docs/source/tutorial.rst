.. _Tutorial:

Quick Start
===========


Install
-------

.. code:: bash

   pip install chemist


MariaDB/MySQL
~~~~~~~~~~~~~

.. code:: bash

   pip install chemist[mysql]
   pip install chemist[mariadb]  # alias to [mysql]


Postgres
~~~~~~~~

.. code:: bash

   pip install chemist[psycopg2]
   pip install chemist[postgres]    # alias to [psycopg2]
   pip install chemist[postgresql]  # alias to [psycopg2]


Declaring a model
-----------------


.. code:: python

    import bcrypt
    from chemist import (
        Model, db, MetaData,
        get_or_create_engine,
    )

    metadata = MetaData()
    engine = get_or_create_engine('sqlite:///example.db')

    CREDIT_CARD_ENCRYPTION_KEY = b'\xb3\x0f\xcc9\xc3\xb1k#\x95j4\xb3\x1f\x08\x98\xd7~6\xff\xceb\xdc\x17vW\xd7\x90\xcf\x82\x9d\xb7j'

    class User(Model):
        table = db.Table(
            'auth_user',
            metadata,
            db.Column('id', db.Integer, primary_key=True),
            db.Column('email', db.String(100), nullable=False, unique=True),
            db.Column('password', db.String(100), nullable=False, unique=True),
            db.Column('created_at', db.DateTime, default=datetime.now),
            db.Column('updated_at', db.DateTime, default=datetime.now),
            db.Column('credit_card', db.String(16)),
        )
        encryption = {
            # transparently encrypt data data in "credit_card" field before storing on DB
            # also transparently decrypt after retrieving data
            'credit_card': CREDIT_CARD_ENCRYPTION_KEY,
        }

        @classmethod
        def create(cls, email, password, **kw):
            email = email.lower()
            password = cls.secretify_password(password)
            return super(User, cls).create(email=email, password=password, **kw)

        def to_dict(self):
            # prevent password and credit-card to be returned in HTTP responses that serialize model data
            data = self.serialize()
            data.pop('password', None)
            data.pop('credit_card', None)
            return data

        @classmethod
        def secretify_password(cls, plain):
            return bcrypt.hashpw(plain, bcrypt.gensalt(12))

        def match_password(self, plain):
            return self.password == bcrypt.hashpw(plain, self.password)

        def change_password(self, old_password, new_password):
            right_password = self.match_password(old_password)
            if right_password:
                secret = self.secretify_password(new_password)
                self.set(password=secret)
                self.save()
                return True

            return False

    metadata.drop_all(engine)
    metadata.create_all(engine)


Creating new records
--------------------

.. code:: python

    data = {
        "email": "octocat@github.com",
        "password": "1234",
    }
    created = User.create(**data)

    assert created.id == 1

    assert created.to_dict() == {
        'id': 1,
    }

    same_user = User.get_or_create(**data)
    assert same_user.id == created.id


Querying
--------

.. code:: python


    user_count = User.count()
    user_list = User.all()

    github_users = User.find_by(email__contains='github.com')
    octocat = User.find_one_by(email='octocat@github.com')

    assert octocat == user_list[0]

    assert octocat.id == 1

    assert user_count == 1


Editing active records
----------------------

.. code:: python


    octocat = User.find_one_by(email='octocat@github.com')

    # modify in memory

    octocat.password = 'much more secure'
    # or ...
    octocat.set(
        password='much more secure',
        email='octocat@gmail.com',
    )

    # save changes (commit transaction and flush db session)
    octocat.save()


    # or ...

    # modify and save changes in a single call
    saved_cat = octocat.update_and_save(
        password='even more secure now',
        email='octocat@protonmail.com',
    )
    assert saved_cat == octocat


Deleting
--------

.. code:: python

    octocat = User.find_one_by(email='octocat@github.com')

    # delete row, commit and flush session
    ghost_cat = octocat.delete()

    # but the copy in memory still has all the data
    assert ghost_cat.id == 1

    # resurrecting the cat
    octocat = ghost_cat.save()
