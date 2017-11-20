#!/usr/bin/env python
# -*- coding: utf-8 -*-


import ast
import os
from setuptools import setup, find_packages


local_file = lambda *f: \
    open(os.path.join(os.path.dirname(__file__), *f)).read()


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
    finder.visit(ast.parse(local_file('flask_chemist', 'version.py')))
    return finder.version


def read_requirements():
    return local_file('requirements.txt').splitlines()


setup(
    name='flask_chemist',
    version=read_version(),
    description='',
    entry_points={
        'console_scripts': ['flask_chemist = flask_chemist.console:entrypoint'],
    },
    author='Gabriel Falcao',
    author_email='gabriel@nacaolivre.org',
    packages=find_packages(exclude=['*tests*']),
    install_requires=read_requirements(),
    include_package_data=True,
    package_data={
        'flask_chemist': ' '.join([
            '*.cfg',
            '*.py',
            '*.rst',
            '*.txt',
        ]),
    },
    zip_safe=False,
)
