from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

import logging
import dateutil.parser as dateutil
from chemist import Model, db
from chemist import (
    metadata,
    set_default_uri,
)


from sqlalchemy import asc, desc
from datetime import timedelta

from flask_app.domain.core import name_from_number
from flask_app.core import autonow, generate_uuid

from flask_app.errors import AuthenticationFailed
from flask_app.errors import UserTokenExpired


engine = set_default_uri('sqlite:///flask_app.db')

logger = logging.getLogger(__name__)


class User(Model):
    table = db.Table(
        'chemist_example_user',
        metadata,
        db.Column('id', db.Integer, primary_key=True, autoincrement=True),
        db.Column('uuid', db.String(36), nullable=False, index=True, unique=True, default=generate_uuid),
        db.Column('email', db.String(255), nullable=False, unique=True),
        db.Column('password', db.String(255), nullable=False),
        db.Column('auth_token', db.Text, nullable=True),
    )

    @classmethod
    def create(cls, email, password, **kw):
        email = email.lower()
        password = cls.secretify_password(password)
        now = autonow().isoformat()
        return super().create(email=email, password=password, created_at=now, updated_at=now, **kw).save()

    def to_dict(self):
        # prevent password to leak inside serialized payloads
        data = self.serialize()
        data.pop('password', None)
        return data

    @classmethod
    def secretify_password(cls, plain):
        return PasswordHasher().hash(plain.encode())

    def match_password(self, plain):
        try:
            PasswordHasher().verify(self.password, plain)
            return True
        except VerifyMismatchError:
            return False

    def logout(self):
        """deletes the user token. Returns self in order to provide a
        `fluent-interface <https://en.wikipedia.org/wiki/Fluent_interface>_`
        """
        return self.set(auth_token=None).save()

    def change_password(self, old_password, new_password):
        right_password = self.match_password(old_password)
        if right_password:
            secret = self.secretify_password(new_password)
            self.set(password=secret)
            self.save()
            return True

        return False

    def authenticate(self, uuid, value):
        t = Token.table
        token = Token.where_one(
            t.c.owner==self.uuid,
            t.c.uuid==uuid,
            t.c.value==value,
        )
        if not token:
            logger.warning(f'no token with uuid {uuid} found')
            raise AuthenticationFailed(f'token not found for email {self.email}')

        if dateutil.parse(token.expires_at) < autonow():
            raise UserTokenExpired(f'{self.email} "{uuid}:{value}"')

        return token

    def reset_token(self):
        return self.set(auth_token=str(uuid.uuid4())).save()
