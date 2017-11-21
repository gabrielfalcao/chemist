.. Flask Chemist documentation master file, created by
   sphinx-quickstart on Sun Nov 19 22:16:39 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Chemist
=======

A simple, flexible and testable active-record powered by SQLAlchemy.



Install
-------

.. code:: bash

   pip install chemist


Basic Usage
-----------


.. code:: python

    from chemist import (
        Model, db, MetaData,
        set_engine,
    )

    metadata = MetaData()
    engine = set_engine('sqlite:///example.db')

    class BlogPost(Model):
          table = db.Table('blog_post',metadata,
              db.Column('id', db.Integer, primary_key=True),
              db.Column('title', db.Unicode(200), nullable=False),
              db.Column('content', db.UnicodeText, nullable=False),
         )

    post1 = BlogPost.create(title='Hello World', content='\n'.join([
        'Introduction...',
        'Supporing Theory 1...',
        'Supporing Theory 2...',
        'Supporing Theory 3...',
        'Conclusion',
    ]))


    for post in BlogPost.all():
        print(post.title, post.id)
