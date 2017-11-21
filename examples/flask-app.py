# -*- coding: utf-8 -*-
import json
from flask import Flask, request
from flask_chemist import (
    Model, db, MetaData,
    set_engine,
)

app = Flask(__name__)

metadata = MetaData()
engine = set_engine('sqlite:///example.db')


class User(Model):
    table = db.Table('user',metadata,
        db.Column('id', db.Integer, primary_key=True),
        db.Column('email', db.String(100), nullable=False, unique=True),
        db.Column('password', db.String(100), nullable=False, unique=True),
        db.Column('created_at', db.DateTime, default=datetime.now),
        db.Column('updated_at', db.DateTime, default=datetime.now)
    )



@app.post("/user")
def create_user():
    email = request.data.get('email')
    password = request.data.get('password')
    user = User.get_or_create(email=email, password=password)
    return json.dumps(user.to_dict()), 201, {'Content-Type': 'application/json'}


@app.post("/user")
def list_users():
    users = User.all()
    data = json.dumps([u.to_dict() for u in users])
    return json.dumps(data), 201, {'Content-Type': 'application/json'}
