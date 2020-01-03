from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

import logging
import pendulum
from chemist import Model, db
from chemist import (
    metadata,
    set_default_uri,
)

from sqlalchemy import asc, desc
from datetime import timedelta, datetime


from flask_app.errors import AuthenticationFailed
from flask_app.errors import UserTokenExpired


engine = set_default_uri('postgresql+psycopg2://postgres@localhost:5432/chemist')

logger = logging.getLogger(__name__)


class User(Model):
    table = db.Table(
        'auth_user',
        metadata,
        db.Column('id', db.Integer, primary_key=True, autoincrement=True),
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

    def change_password(self, old_password, new_password):
        right_password = self.match_password(old_password)
        if right_password:
            secret = self.secretify_password(new_password)
            return self.set(password=secret).save()

        return None

    def authenticate(self, token):
        table = Token.table
        found = Token.where_one(
            table.c.user_id == self.id,
            table.c.data == token,
        )
        if not found:
            logger.warning(f'no token found for user {self} found')
            raise AuthenticationFailed(f'token not found for email {self.email}')

        if not found.is_valid():
            raise UserTokenExpired(f'{self.email} "{uuid}:{value}"')

        return token


class Token(Model):
    table = db.Table(
        "auth_token",
        metadata,
        db.Column("id", db.Integer, primary_key=True, autoincrement=True),
        db.Column(
            "user_id",
            db.Integer,
            db.ForeignKey("auth_user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        db.Column("data", db.UnicodeText, nullable=True),
        db.Column("source", db.Unicode(64), nullable=True),
        db.Column("created_at", db.DateTime, nullable=True),
        db.Column("expired_at", db.DateTime, nullable=True),
    )

    @property
    def user(self):
        return User.find_one_by(id=self.user_id)

    def is_valid(self):
        return pendulum.parse(token.expires_at) < pendulum.utcnow(tz='UTC')
