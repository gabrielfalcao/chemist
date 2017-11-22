#!/usr/bin/env python
# -*- coding: utf-8 -*-

"A simple, flexible and testable active-record powered by SQLAlchemy."


import ast
import os
from setuptools import setup, find_packages


local_file = lambda *f: open(os.path.join(os.path.dirname(__file__), *f)).read()


class VersionFinder(ast.NodeVisitor):
    VARIABLE_NAME = 'version'

    def __init__(self):
        self.version = None

    def visit_Assign(self, node):
        try:
            if node.targets[0].id == self.VARIABLE_NAME:
                self.version = node.value.s
        except:
            pass


def read_version():
    finder = VersionFinder()
    finder.visit(ast.parse(local_file('chemist', 'version.py')))
    return finder.version


def read_requirements():
    return local_file('requirements.txt').splitlines()


def read_readme():
    """Read README content.
    If the README.rst file does not exist yet
    (this is the case when not releasing)
    only the short description is returned.
    """
    try:
        return local_file('README.rst')
    except IOError:
        return __doc__


setup(
    name='chemist',
    version=read_version(),
    description=read_readme(),
    author='Gabriel Falcao',
    author_email='gabriel@nacaolivre.org',
    maintainer='Gabriel Falcao',
    maintainer_email='gabriel@nacaolivre.org',
    entry_points={
        'console_scripts': ['chemist = chemist.console:entrypoint'],
    },
    author='Gabriel Falcao',
    author_email='gabriel@nacaolivre.org',
    packages=find_packages(exclude=['*tests*']),
    install_requires=read_requirements(),
    test_suite='nose.collector',
    include_package_data=True,
    description=__doc__,
    long_description=read_readme(),
    package_data={
        'chemist': ' '.join([
            '*.cfg',
            '*.py',
            '*.rst',
            '*.txt',
        ]),
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: Implementation :: CPython',
    ]
    zip_safe=False,
)
