# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.
# This code is distributed under the two-clause BSD License.

from __future__ import unicode_literals

import glob
import io
import os

from . import compat
from .compat import configparser

# Constant indicating that no namespace should be prefixed to environment variables.
NO_NAMESPACE = object()


class NotFound(KeyError):
    """Raised when a key is not found in a configuration source."""


class SectionDictFinder(object):
    """Simple finder finding key in a 1-level nested dictionary

    The looked-up keys should follow the "section.entry" format, split on
    the first found dot ('.').
    In the absence of any dot, the key will be looked up as "DEFAULT.key".

    For example:
        >>> finder = SectionDictFinder({'DEFAULT': {'foo': 'bar'}, 'db': {'password': 'S3cr3t'}})
        >>> finder.find('foo') == finder.find('DEFAULT.foo') == 'bar'
        True
        >>> finder.find('db.password')
        S3cr3t
        >>> finder.find('any_ot.her_key')
        Traceback (most recent call last):
        ...
        raise NotFound()
        getconf.finders.NotFound
    """

    def __init__(self, data):
        self.data = data

    def split_section_key(self, key):
        if '.' in key:
            return key.split('.', 1)
        return 'DEFAULT', key

    def find(self, key):
        section, key = self.split_section_key(key)
        try:
            return self.data[section][key]
        except KeyError:
            raise NotFound()


class NamespacedEnvFinder(object):
    """Finder looking inside os.environ

    The looked-up keys are expected to follow the "section.entry" format, split on
    the first found dot ('.').

    The corresponding env var will then be NAMESPACE_SECTION_ENTRY.
    If the looked-up key has no section (no '.'), NAMESPACE_KEY will be looked up.

    If the specified namespace is getconf.NO_NAMESPACE, the matching env vars will
    be SECTION_ENTRY or KEY depending on wheither the key's section is defined or not.
    """

    def __init__(self, namespace):
        self.namespace = namespace

    def env_key(self, key):
        if '.' in key:
            section, key = key.split('.', 1)
        else:
            section = ''
        if section:
            args = (section, key)
        else:
            args = (key,)
        if self.namespace is not NO_NAMESPACE:
            args = (self.namespace,) + args
        return '_'.join(arg.upper() for arg in args).replace('-', '_')

    def find(self, key):
        env_key = self.env_key(key)
        try:
            value = os.environ[env_key]
        except KeyError:
            raise NotFound()

        if compat.PY2:  # Bytes in PY2, text in PY3.
            value = value.decode('utf-8')
        return value


class MultiINIFilesParserFinder(object):
    """Finder looking inside a list of provided INI files.

    The looked-up keys should follow the "section.entry" format, split on
    the first found dot ('.').
    In the absence of any dot, the key will be looked up as "DEFAULT.key".

    ``config_files`` accepts directories and glob: directories are interpreted as
    the glob `some_dir/*` and globs are replaced by the matching files list sorted by names.

    Later files take precedence over previous ones.
    Files are parsed without interpolation.
    """

    def __init__(self, config_files):
        self.parser = compat.get_no_interpolation_config_parser()
        self.search_files = []

        for path in config_files:
            if path is None:
                continue
            # Handle '~/.foobar.conf'
            path = os.path.abspath(os.path.expanduser(path))
            if os.path.isdir(path):
                path = os.path.join(path, '*')

            self.search_files.append(path)

        final_config_files = []
        for path in self.search_files:
            directory_files = glob.glob(path)
            if directory_files:
                # Reverse order: final_config_files is parsed from left to right,
                # so 99_foo naturally takes precedence over 10_base
                final_config_files.extend(sorted(directory_files))

        # ConfigParser's precedence rules say "later files take precedence over previous ones".
        # Since our final_config_files are sorted from least important to most important,
        # that's exactly what we need.
        self.found_files = self.parser.read(final_config_files)

    def split_section_key(self, key):
        if '.' in key:
            return key.split('.', 1)
        return 'DEFAULT', key

    def find(self, key):
        section, key = self.split_section_key(key)
        try:
            value = self.parser.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            raise NotFound()

        if compat.PY2:  # Bytes in PY2, text in PY3
            value = value.decode('utf-8')
        return value


class FileContentFinder(object):
    """Simple finder finding key in a directory by matching filenames

    If the specified ``directory`` contains a file named ``key``, its content
    is decoded using the specified ``encoding`` and returned as value.
    """

    def __init__(self, directory, encoding='utf-8'):
        self.directory = directory
        self.encoding = encoding

    def find(self, key):
        path = os.path.join(self.directory, key)
        if os.path.isfile(path):
            with io.open(path, encoding=self.encoding) as f:
                return f.read()
        raise NotFound()
