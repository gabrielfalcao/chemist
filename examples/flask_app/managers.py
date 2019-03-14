# -*- coding: utf-8 -*-
from flask_app.core import autonow

from flask_app.errors import AuthenticationFailed
from flask_app.errors import UserNotFound

from flask_app.models import User


class UserManager(object):
    """
    usage:

    ::

        users = UserManager()
        user = users.add('some@email.com', 'clear-password')
        users.authenticate(
        users = UserManager()

    """
    def add(self, email, password):
        return User.create(email=email, password=password).save()

    def by_email(self, email, fail=True):
        found = User.find_one_by(email=email)
        if fail and not found:
            raise UserNotFound(email)

        return found

    def remove(self, email):
        found = User.find_one_by(email=email)
        if not found:
            raise UserNotFound(email)

        found.logout().delete()
        return True

    def login(self, email, password):
        user = self.by_email(email, fail=False)
        if not user:
            raise AuthenticationFailed(f'User not found for {email}')

        if not user.match_password(password):
            raise AuthenticationFailed(f'invalid password for {email}')

        return user.create_token()

    def logout(self, email):
        return self.by_email(email).logout()

    def authenticate(self, email, uuid, value):
        return self.by_email(email).authenticate(uuid, value)
