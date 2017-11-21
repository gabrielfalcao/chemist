.. Flask Chemist documentation master file, created by
   sphinx-quickstart on Sun Nov 19 22:16:39 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Chemist
=======

A simple, flexible and testable active-record powered by SQLAlchemy.

.. image:: https://readthedocs.org/projects/chemist/badge/?version=latest
   :target: http://chemist.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. |Build Status| image:: https://travis-ci.org/gabrielfalcao/sure.png?branch=master
   :target: https://travis-ci.org/gabrielfalcao/sure
   :alt: Build Status
.. |PyPI package version| image:: https://badge.fury.io/py/sure.svg
   :target: https://badge.fury.io/py/sure
   :alt: PyPI versions from fury.io
.. |PyPI python versions| image:: https://img.shields.io/pypi/pyversions/sure.svg
   :target: https://pypi.python.org/pypi/sure
   :alt: PyPI versions from shields.io
.. |Join the chat at https://gitter.im/gabrielfalcao/sure| image:: https://badges.gitter.im/gabrielfalcao/sure.svg
   :target: https://gitter.im/gabrielfalcao/sure?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
   :alt: Gitter Link



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
