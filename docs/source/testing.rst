.. _Testing:

Testing
=======


The example below uses the module `testing.postgresql
<https://pypi.org/project/testing.postgresql/>`_ to run each test case
in an isolated postgres server instance all you need is the postgres
binaries available in the host machine.


``test_models.py``
------------------

.. code:: python


   import unittest
   import testing.postgresql
   from chemist import set_default_uri
   from models import User


   class UserModelTestCase(unittest.TestCase):
       def setUp(self):
           self.postgresql = testing.postgresql.Postgresql()
           set_default_uri(self.postgresql.url())

       def tearDown(self):
           self.postgresql.stop()

       def test_authentication(self):
           # Given a user with a hardcoded password
           foobar = User.create('foo@bar.com', '123insecure')

           # When I match the password
           matched = foobar.match_password('123insecure')

           # Then it should have matched
           assert matched, f'user {foobar} did not match password 123insecure'


       def test_change_password(self):
           # Given a user with a hardcoded password
           foobar = User.create('foo@bar.com', '123insecure')

           # When I change the password
           changed = foobar.change_password('123insecure', 'newPassword')

           # Then it should have succeeded
           assert matched, f'failed to change password for {foobar}'

           # And should authenticate with the new password
           assert foobar.match_password('newPassword'), f'user {foobar} did not match password newPassword'



``models.py``
-------------

.. code:: python

    import bcrypt
    from chemist import (
        Model, db, metadata
        set_default_uri,
    )

    engine = set_default_uri('sqlite:///example.db')

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
