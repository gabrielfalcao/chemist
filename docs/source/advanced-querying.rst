.. _Advanced Querying:

Advanced Querying
=================


SELECT * FROM table WHERE ...
-----------------------------


Use the methods :py:meth:`~chemist.managers.where_one` and
:py:meth:`~chemist.managers.where_many` with the same clause accepted
by :py:meth:`~sqlalchemy.sql.expression.Select.where`.



.. code-block:: python
   :emphasize-lines: 34-40, 44-45

   from datetime import datetime

   from sqlalchemy import asc, desc

   from chemist import (
       Model, db,
       get_or_create_engine,
   )
   from chemist import metadata  # use chemist-managed metadata

   def generate_uuid():
       return str(uuid.uuid4())


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


.. seealso:: :py:meth:`~chemist.managers.where_one` and
          :py:meth:`~chemist.managers.where_many` **optionally take**
          an ``order_by=`` keyword-argument, which must be a tuple of ``asc()`` or ``desc()`` columns.
