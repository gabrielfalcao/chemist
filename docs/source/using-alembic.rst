.. _Using Alembic:

Using Alembic
=============


Creating tables
---------------

.. code:: python

    def upgrade():
        op.create_table(
            'user',
            sa.Column('id', sa.Integer, primary_key=True, nullable=False),
            sa.Column('uuid', sa.String(32), nullable=False),
            sa.Column('email', sa.String(254)),
            sa.Column('password', sa.String(128)),
            sa.Column('creation_date', sa.DateTime, nullable=False),
            sa.Column('activation_date', sa.DateTime, nullable=True),
            sa.Column('json_data', sa.Text, nullable=True),
            sa.Column('last_access_date', sa.DateTime, nullable=True),
            sa.Column('password_change_date', sa.DateTime, nullable=True),
        )


    def downgrade():
        op.drop_table('user')


Modifying Columns
-----------------

.. code:: python

    def upgrade():
        op.alter_column('user', 'json_data', existing_type=db.Text, type_=db.LargeBinary)


    def downgrade():
        op.alter_column('user', 'json_data', existing_type=db.LargeBinary, type_=db.Text)



``script.py.mako``
------------------

.. code:: python


    # -*- coding: utf-8 -*-
    # flake8: noqa
    """${message}

    Revision ID: ${up_revision}
    Revises: ${down_revision}
    Create Date: ${create_date}

    """

    # revision identifiers, used by Alembic.
    revision = ${repr(up_revision)}
    down_revision = ${repr(down_revision)}

    from datetime import datetime
    from alembic import op
    import sqlalchemy as db
    ${imports if imports else ""}



    def DefaultForeignKey(field_name, parent_field_name,
                          ondelete='CASCADE', nullable=False, **kw):
        return db.Column(field_name, db.Integer,
                         db.ForeignKey(parent_field_name, ondelete=ondelete),
                         nullable=nullable, **kw)


    def PrimaryKey(name='id'):
        return db.Column(name, db.Integer, primary_key=True)


    def now():
        return datetime.utcnow()


    def upgrade():
        ${upgrades if upgrades else "pass"}


    def downgrade():
        ${downgrades if downgrades else "pass"}
