# -*- coding: utf-8 -*-
# Copyright (c) 2011-2014 Polyconseil SAS.
# This code is distributed under the two-clause BSD License.

from __future__ import unicode_literals

import collections
import glob
import logging
import warnings
import os

from . import compat
from .compat import configparser


logger = logging.getLogger(__name__)

# Avoid issue with 'no handler found for...' when called before logging setup.
if os.environ.get('LOG_TO_STDERR', '0') == 1:
    logger.addHandler(logging.StreamHandler())
else:
    logger.addHandler(compat.NullHandler())


ConfigKey = collections.namedtuple('ConfigKey', ['section', 'entry', 'envvar', 'doc'])


class NotFound(KeyError):
    """Raised when a key is not found in a configuration source."""


class ConfigGetter(object):
    """A simple wrapper around ConfigParser + os.environ.

    Designed for use in a settings.py file.

    Usage:
        >>> config = ConfigGetter('blusers', ['/etc/blusers/settings.ini'])
        >>> x = config.get('psql.server', 'localhost:5432')
        'localhost:5432'

    With the above ``ConfigGetter``:
    - Calls to get('psql.server', 'foo') will look at:
        - Environment key BLUSERS_PSQL_SERVER
        - Key 'server' from section 'pqsl' of config file given in env
          BLUSERS_CONFIG, if provided
        - Key 'server' from section 'psql' of config file
          ``/etc/blusers/settings.ini``
        - Key 'psql' in key 'server' of default config dict
        - The provided default

    - Calls to get('secret_key') will look at:
        - Environment key BLUSERS_SECRET_KEY
        - Key 'secret_key' from section 'DEFAULT' of config file given in env
          BLUSERS_CONFIG, if provided
        - Key 'secret_key' from section 'DEFAULT' of config file
          ``/etc/blusers/settings.ini``
        - Key 'secret_key' of default config dict
        - The empty string
    """

    def __init__(self, namespace, config_files=(), defaults=None):
        self.parser = configparser.ConfigParser()
        self.seen_keys = set()

        self.namespace = namespace
        self.defaults = defaults or {}

        final_config_files = []
        for path in config_files:
            # Handle '~/.foobar.conf'
            path = os.path.abspath(os.path.expanduser(path))
            if os.path.isdir(path):
                directory_files = glob.glob(os.path.join(path, '*'))
                # Reverse order: final_config_files is parsed from left to right,
                # so 99_foo naturally takes precedence over 10_base
                final_config_files.extend(sorted(directory_files))
            else:
                final_config_files.append(path)

        extra_config_file = os.environ.get(self._env_key('config'), '')
        if extra_config_file:
            final_config_files.append(extra_config_file)

        self.search_files = final_config_files
        # ConfigParser's precedence rules say "later files take precedence over previous ones".
        # Since our final_config_files are sorted from least important to most important,
        # that's exactly what we need.
        self.found_files = self.parser.read(self.search_files)

        logger.info(
            "Successfully loaded configuration from files %r (searching in %r)",
            self.found_files, self.search_files,
        )

    def _env_key(self, key, section=''):
        if section:
            args = (self.namespace, section, key)
        else:
            args = (self.namespace, key)
        return '_'.join(arg.upper() for arg in args)

    def _read_env(self, key):
        """Handle environ-related logic."""
        try:
            value = os.environ[key]
        except KeyError:
            raise NotFound()

        if compat.PY2:  # Bytes in PY2, text in PY3.
            value = value.decode('utf-8')
        return value

    def _read_parser(self, config_section, key):
        """Handle configparser-related logic."""
        try:
            value = self.parser.get(config_section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            raise NotFound()

        if compat.PY2:  # Bytes in PY2, text in PY3
            value = value.decode('utf-8')
        return value

    def _get(self, env_key, section, key, default=''):

        try:
            return self._read_env(env_key)
        except NotFound:
            pass

        try:
            return self._read_parser(section, key)
        except NotFound:
            pass

        try:
            return self.defaults[section][key]
        except KeyError:
            pass

        return default

    def get(self, key, default='', doc=''):
        """Fetch a value from the various sources."""
        if '.' in key:
            section, key = key.split('.', 1)
        else:
            section = ''
        env_key = self._env_key(key, section=section)
        config_section = section or 'DEFAULT'

        value = self._get(env_key=env_key, section=config_section, key=key, default=default)

        self.seen_keys.add(ConfigKey(section=config_section, entry=key, envvar=env_key, doc=doc))

        return value

    def getlist(self, key, default='', doc=''):
        """Retrieve a value as a list.

        Splits on ',', strips entries and return only non-empty values.
        """
        value = self.get(key, default=default, doc=doc)
        values = [entry.strip() for entry in value.split(',')]
        values = [entry for entry in values if entry]
        return values

    def getbool(self, key, default=False, doc=''):
        """Retrieve a value as a boolean.

        Accepts the following values as 'True':
            on, yes, true, 1
        """
        value = self.get(key, default=compat.text_type(default), doc=doc)
        return compat.text_type(value).lower() in ('on', 'true', 'yes', '1')

    def getint(self, key, default=False, doc=''):
        """Retrieve a value as an integer."""
        value = self.get(key, default=default, doc=doc)
        return int(value)

    def get_section(self, section_name):
        """Return a dict-like object for the chosen section."""
        return ConfigSectionGetter(self, section_name)

    def list_keys(self):
        """Return the list of used keys.

        Returns:
            list of ConfigKey (section, entry, envvar tuple)
        """
        return sorted(self.seen_keys)


class ConfigSectionGetter(object):
    """Proxy around a section."""
    def __init__(self, config, section):
        self.base_config = config
        self.section = section

    def __getitem__(self, key):
        return self.base_config.get('%s.%s' % (self.section, key))
