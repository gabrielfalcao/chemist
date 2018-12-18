# -*- coding: utf-8 -*-
import uuid
from sure import scenario
from mock import Mock
from datetime import datetime
from decimal import Decimal
from sqlalchemy import asc, desc
from chemist import (
    Model, db, MetaData,
    get_or_create_engine,
)

metadata = MetaData()

def generate_uuid():
    return str(uuid.uuid4())


def reset_db(context):
    engine = get_or_create_engine('postgresql+psycopg2://localhost/chemist')  # in memory db
    metadata.drop_all(engine)
    metadata.create_all(engine)


clean_db = scenario(reset_db, reset_db)

def autonow():
    return datetime.utcnow()

class Task(Model):
    table = db.Table(
        'advanced_querying_task',
        metadata,
        db.Column('id', db.Integer, primary_key=True),
        db.Column('uuid', db.String(36), nullable=False, index=True, default=generate_uuid),
        db.Column('name', db.UnicodeText, nullable=False),
        db.Column('done_at', db.DateTime),
        db.Column('updated_at', db.DateTime, default=autonow),
    )

    @classmethod
    def list_pending(model, *expressions):
        table = model.table
        order_by = (desc(table.c.updated_at), )
        return model.objects().where_many(
            model.table.c.done_at==None,
            *expressions,
            order_by=order_by,
        )

    @classmethod
    def get_by_uuid(model, uuid):
        table = model.table
        return model.objects().where_one(model.table.c.uuid==uuid)


@clean_db
def test_create_task(context):
    "Test query "

    a_uuid = generate_uuid()

    t1 = Task.create(uuid=a_uuid, name='write a task management service')
    t2 = Task.create(name='throw away trash')
    t3 = Task.create(name='watch GoT')
    t4 = Task.create(name='watch Big Bang Theory')
    t5 = Task.create(name='build UI for task management')


    fresh_t1 = Task.get_by_uuid(a_uuid)
    fresh_t1.should.equal(t1)

    Task.list_pending().should.equal([
        t5,
        t4,
        t3,
        t2,
        t1,
    ])
