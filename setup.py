#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Polyconseil SAS
# This software is distributed under the two-clause BSD license.

import codecs
import os
import re
import sys

from setuptools import setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    init_path = os.path.join(root_dir, *(package_components + ['__init__.py']))
    with codecs.open(init_path, 'r', 'utf-8') as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.0'


PACKAGE = 'getconf'


setup(
    name=PACKAGE,
    version=get_version(PACKAGE),
    description="getconf, a versatile configuration lib for Python projects",
    long_description=''.join(codecs.open('README.rst', 'r', 'utf-8').readlines()),
    author="Polyconseil",
    author_email="opensource+%s@polyconseil.fr" % PACKAGE,
    license="BSD",
    keywords=['configuration', 'environment', 'setup', 'getconf', 'config'],
    url="https://github.com/Polyconseil/%s/" % PACKAGE,
    download_url="https://pypi.python.org/pypi/%s/" % PACKAGE,
    packages=[PACKAGE],
    platforms=["OS Independent"],
    install_requires=codecs.open('requirements.txt', 'r', 'utf-8').readlines(),
    setup_requires=[
        'setuptools>=0.8',
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Systems Administration",
    ],
    test_suite='tests',
)
