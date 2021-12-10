import glob
import os
import sys
from distutils.core import setup
from typing import List
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


def get_version(filename):
    import ast
    version = None
    with open(filename) as f:
        for line in f:
            if line.startswith('__version__'):
                version = ast.parse(line).body[0].value.s
                break
        else:
            raise ValueError('No version found in %r.' % filename)
    if version is None:
        raise ValueError(filename)
    return version


setuptools.setup(
    name="datalite3",
    version=get_version("datalite3/__init__.py"),
    author="Andrea F. Daniele",
    author_email="afdaniele@ttic.edu",
    description="A small package that binds dataclasses to an sqlite3 database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/afdaniele/datalite3",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)