# -*- coding: utf-8 -*-
# Copyright (c) 2011-2014 Polyconseil SAS.
# This code is distributed under the two-clause BSD License.

from __future__ import unicode_literals

import collections
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
        - The provided default

    - Calls to get('secret_key) will look at:
        - Environment key BLUSERS_SECRET_KEY
        - Key 'secret_key' from section 'DEFAULT' of config file given in env
          BLUSERS_CONFIG, if provided
        - Key 'secret_key' from section 'DEFAULT' of config file
          ``/etc/blusers/settings.ini``
        - The empty string
    """
    def __init__(self, namespace, config_files=(), *old_style_config_files):
        self.namespace = namespace
        self.parser = configparser.ConfigParser()
        self.seen_keys = set()

        if isinstance(config_files, compat.string_types):
            warnings.warn(
                "Using %s is deprecated and will be removed in getconf 1.2.0; please use %s instead" % (
                    "ConfigGetter(namespace, 'settings_1.ini', 'settings_2.ini', ...)",
                    "ConfigGetter(namespace, ['settings_1.ini', 'settings_2.ini', ...])",
                ),
                DeprecationWarning,
                stacklevel=2,
            )
            config_files = (config_files, ) + old_style_config_files

        extra_config_file = os.environ.get(self._env_key('config'), '')
        search_files = list(config_files) + [extra_config_file]

        self.search_files = tuple(f for f in search_files if f)
        self.found_files = tuple(self.parser.read(self.search_files))

        logger.info(
            "Successfully loaded configuration from files %s (searching in %s)",
            ', '.join(self.found_files),
            ', '.join(self.search_files),
        )

    def _env_key(self, *args):
        args = (self.namespace,) + args
        return '_'.join(arg.upper() for arg in args)

    def _read_env(self, key, default):
        """Handle environ-related logic."""
        try:
            env_value = os.environ[key]
        except KeyError:
            return default

        if compat.PY2:  # Bytes in PY2, text in PY3.
            env_value = env_value.decode('utf-8')
        return env_value

    def _read_parser(self, config_section, key, default):
        """Handle configparser-related logic."""
        try:
            if compat.PY2:
                value = self.parser.get(config_section, key).decode('utf-8')
            else:
                value = self.parser.get(config_section, key, fallback=default)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
        return value

    def get(self, key, default='', doc=''):
        if '.' in key:
            section, key = key.split('.', 1)
        else:
            section = ''

        value = default

        # Try config file
        config_section = section or 'DEFAULT'
        value = self._read_parser(config_section, key, default=value)

        # Try environ
        if section:
            env_key = self._env_key(section, key)
        else:
            env_key = self._env_key(key)

        value = self._read_env(env_key, value)

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
