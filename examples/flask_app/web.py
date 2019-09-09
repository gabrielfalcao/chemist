# -*- coding: utf-8 -*-
import json
from flask import Flask, request

from flask_app.models import User, metadata, engine


def json_response(data, code=200):
    return json.dumps(data), code, {'Content-Type': 'application/json'}


def error_response(msg, code=400):
    return json_response({"error": msg}, code)


def authenticated(func):
    return func


@app.post("/signup")
def create_user():
    email = request.data.get('email')
    password1 = request.data.get('password1')
    password2 = request.data.get('password2')

    if password1 != password2:
        return error_response('passwords do not match', 400)

    user = User.get_or_create(email=email, password=password)
    return json.dumps(user.to_dict()), 201, {'Content-Type': 'application/json'}


@app.post("/login")
def login():
    email = request.data.get('email')
    password = request.data.get('password')

    user = User.get(email=email)
    if not user or not user.match_password(password):
        return error_response('authentication error', 401)

    return json_response(user.to_dict())


@app.get("/users")
@authenticated
def list_users():
    users = User.all()
    data = [{'email': u.email, 'id': u.id} for u in users]
    return json_response(data)


def prepare_db_and_run_application():
    metadata.create_all(engine, verify_first=True)
    app.run(debug=True)


if __name__ == '__main__':
    prepare_db_and_run_application()
