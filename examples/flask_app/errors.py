# -*- coding: utf-8 -*-

class InternalFailure(Exception):
    "base class for all errors pertaining to the flask application"

class UIException(Exception):
    "base class for all exceptions that can be shown to a user"

class UserNotFound(UIException):
    "raised when user is not found"

class AuthenticationFailed(UIException):
    "raised when user is not found or password mismatched"

class UserTokenExpired(AuthenticationFailed):
    "raised when given token is expired"

class InvalidQuadrant(InternalFailure):
    "raised when an invalid quadrant number or name was used"
