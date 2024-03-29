# Copyright (c) Polyconseil SAS. All rights reserved.
# This code is distributed under the two-clause BSD License.

import collections
import datetime
import enum
import logging
import operator
from pathlib import Path
import warnings

from . import finders


logger = logging.getLogger(__name__)

# Avoid issue with 'no handler found for...' when called before logging setup.
logger.addHandler(logging.NullHandler())


_ConfigKey = collections.namedtuple(
    'ConfigKey',
    ['key', 'doc', 'default', 'type_hint']
)


class ConfigKey(_ConfigKey):

    def __hash__(self):
        if self.type_hint == 'list' and self.default is not None:
            # Make sure we can hash default
            default = tuple(self.default)
        else:
            default = self.default
        return hash((self.key, self.doc, default, self.type_hint))


class InvalidKey(Exception):
    """Raised when an invalid key is requested"""


class BaseConfigGetter:
    """Base class used to define custom ConfigGetter

    It expects a list of finder objects implementing a ``find(key)`` method that should
    either return a string if the key was found or raise finders.NotFound() otherwise.
    Finders will be called in the specified order.

    If provided, key_validator must be a callable that raises InvalidKey on invalid keys.
    """

    def __init__(self, *config_finders, key_validator=None):
        self.finders = config_finders
        self.seen_keys = set()
        self.key_validator = key_validator

    def _read(self, key, default):
        for finder in self.finders:
            try:
                return finder.find(key)
            except finders.NotFound:
                pass

        return default

    def _get(self, key, default, doc, type_hint=''):
        if self.key_validator is not None:
            self.key_validator(key)
        value = self._read(key=key, default=default)
        self.seen_keys.add(ConfigKey(key=key, doc=doc, default=default, type_hint=type_hint))
        return value

    def get(self, key, default='', doc=''):
        """Compatibility method to retrieve values from various import sources. Soon deprecated."""
        assert (
            default is None or isinstance(default, str)
        ), f'get("{key}", {repr(default)}) has an invalid default value type.'
        warnings.warn("Use of get() directly is deprecated. Use .getstr() instead", DeprecationWarning)
        return self._get(key, default=default, doc=doc)

    def getstr(self, key, default='', doc=''):
        """Retrieve a value as a string."""
        assert (
            default is None or isinstance(default, str)
        ), f'getstr("{key}", {repr(default)}) has an invalid default value type.'
        return self._get(key, default=default, doc=doc, type_hint='str')

    def getlist(self, key, default=(), doc='', sep=','):
        """Retrieve a value as a list.

        Splits on ',', strips entries and returns only non-empty values.
        """
        assert (
            isinstance(default, str) or
            default is None or isinstance(default, (list, tuple))
        ), f'getlist("{key}", {repr(default)}) has an invalid default value type.'
        if isinstance(default, str):
            warnings.warn(
                "Use of a string as default value in getlist() is deprecated. Use list of strings instead",
                DeprecationWarning
            )
        if default is not None and any(not isinstance(value, str) for value in default):
            warnings.warn(
                "List of non-string as default is deprecated. Use list of strings instead",
                DeprecationWarning
            )
        value = self._get(key, default=default, doc=doc, type_hint='list')
        if isinstance(value, str):
            values = [entry.strip() for entry in value.split(sep)]
            values = [entry for entry in values if entry]
            return values
        elif value is None:
            return None
        return list(value)

    def getbool(self, key, default=False, doc=''):
        """Retrieve a value as a boolean.

        Accepts the following values as 'True':
            on, yes, true, 1
        """
        assert (
            default is None or isinstance(default, bool)
        ), f'getlist("{key}", {repr(default)}) has an invalid default value type.'
        value = self._get(key, default=default, doc=doc, type_hint='bool')
        if value is None:
            return None
        return str(value).lower() in ('on', 'true', 'yes', '1')

    def getint(self, key, default=0, doc=''):
        """Retrieve a value as an integer."""
        assert (
            default is None or isinstance(default, int)
        ), f'getint("{key}", {repr(default)}) has an invalid default value type.'
        value = self._get(key, default=default, doc=doc, type_hint='int')
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            logger.exception("Unable to cast %s as integer for the key %s.", repr(value), key)
            raise

    def getfloat(self, key, default=0.0, doc=''):
        """Retrieve a value as a float."""
        assert (
            default is None or isinstance(default, float)
        ), f'getfloat("{key}", {repr(default)}) has an invalid default value type.'
        value = self._get(key, default=default, doc=doc, type_hint='float')
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            logger.exception("Unable to cast %s as float for the key %s.", repr(value), key)
            raise

    def gettimedelta(self, key, default='0d', doc=''):
        """Retrieve a value as a datetime.timedelta."""
        assert (
            default is None or isinstance(default, str)
        ), f'gettimedelta("{key}", {repr(default)}) has an invalid default value type.'
        value = self._get(key, default=default, doc=doc, type_hint='timedelta')
        if value is None:
            return None

        conversion = {'d': 'days', 'h': 'hours', 'm': 'minutes', 's': 'seconds'}
        value, unit = value[:-1], value[-1:]
        try:
            value = float(value)
            unit = conversion[unit]
        except ValueError:
            logger.exception("Unable to cast %s as float for the key %s.", repr(value), key)
            raise
        except KeyError:
            fmt = "%r is not a valid unit for the key %s (acceptable values are %s)."
            args = (unit, key, ', '.join(conversion.keys()))
            logger.exception(fmt, *args)
            raise ValueError(fmt % args)
        else:
            return datetime.timedelta(**{unit: value})

    def getpath(self, key, default=Path('.'), doc=''):
        assert (
            default is None or isinstance(default, (Path, str))
        ), f'getpath("{key}", {default!r}) has an invalid default value type.'
        value = self._get(key, default=default, doc=doc, type_hint='pathlib.Path')
        if value is None:
            return None
        try:
            return Path(value)
        except TypeError:  # not raising ValueError
            logger.exception("Unable to cast %r as Path for the key %s.", value, key)
            raise

    def getenum(self, key, default=None, doc='', enum_class=None):
        if enum_class is None and isinstance(default, enum.Enum):
            enum_class = type(default)
        assert (
            enum_class is not None and (default is None or (
                enum_class is not None and issubclass(enum_class, enum.Enum)
            ))
        ), 'getenum("{}", {!r}, enum_class={!r}) is missing a default value or this one has an invalid type.'.format(
            key, default, enum_class
        )
        value = self._get(key, default=default, doc=doc, type_hint='enum.Enum')
        if value is None:
            return None
        if isinstance(value, enum_class):
            return value
        enum_value_type = type(next(member for member in enum_class).value)
        if not isinstance(value, enum_value_type):
            # E.g. the value comes from a file or an environment variable and is a string but our enum expects int
            # values.
            try:
                value = enum_value_type(value)
            except ValueError:
                logger.exception("Unable to cast %s as %r for the key %s.", repr(value), enum_value_type, key)
        try:
            return enum_class(value)
        except ValueError:
            logger.exception('Expected key "%s" to be one of %s, got %r.', key, [member.value for member in enum_class], value)
            raise


def section_validator(key):
    if "." not in key:
        raise InvalidKey(f"{key} should contain a section")


class ConfigGetter(BaseConfigGetter):
    """A simple wrapper around ConfigParser + os.environ.

    Designed for use in a settings.py file.

    Usage:
        >>> config = ConfigGetter('blusers', ['/etc/blusers/settings.ini'])
        >>> x = config.getstr('psql.server', 'localhost:5432')
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

    def __init__(self, namespace, config_files=(), defaults=None, mandatory_section=False):
        self._env_finder = finders.NamespacedEnvFinder(namespace)

        config_files = list(config_files)
        try:
            config_files.append(self._env_finder.find('config'))
        except finders.NotFound:
            pass
        self._parser_finder = finders.MultiINIFilesParserFinder(config_files)
        logger.info(
            "Successfully loaded configuration from files %r (searching in %r)",
            self._parser_finder.found_files, self._parser_finder.search_files,
        )
        key_validator = section_validator if mandatory_section else None
        super().__init__(
            self._env_finder,
            self._parser_finder,
            finders.SectionDictFinder(defaults or {}),
            key_validator=key_validator,
        )

    @property
    def search_files(self):
        return self._parser_finder.search_files

    @property
    def found_files(self):
        return self._parser_finder.found_files

    def get_section(self, section_name):
        """Return a dict-like object for the chosen section."""
        return ConfigSectionGetter(self, section_name)

    def list_keys(self):
        """Return the list of used keys.

        Returns:
            list of ConfigKey
        """
        return sorted(self.seen_keys)

    def get_ini_template(self):
        """Export commented INI file content mapping to the defaults"""
        section_to_keys = collections.defaultdict(list)
        for config_key in self.seen_keys:
            section, entry = self._parser_finder.split_section_key(config_key.key)
            envvar = self._env_finder.env_key(config_key.key)

            # Remove any new line in doc
            one_line_doc = ' '.join(config_key.doc.split())
            doc_part = (' - %s' % one_line_doc) if one_line_doc else ''

            if config_key.type_hint == 'list':
                default = ', '.join(config_key.default)
            elif config_key.type_hint == 'bool':
                default = 'on' if config_key.default else 'off'
            else:
                default = str(config_key.default)
            default_str = ' %s' % default if default else ''

            entry_str = '; {envvar} - type={type_hint}{doc_part}\n;{entry} ={default_str}'.format(
                envvar=envvar,
                type_hint=config_key.type_hint,
                doc_part=doc_part,
                entry=entry,
                default_str=default_str,
            )
            section_to_keys[section].append((entry, entry_str))

        parts = []
        for section, keys in sorted(section_to_keys.items()):
            parts.append('[%s]' % section)
            for _entry, entry_str in sorted(keys, key=operator.itemgetter(0)):
                parts.append(entry_str)
            # Add a newline between sections
            parts.append('')
        # But drop last newline
        return '\n'.join(parts[:-1])


class ConfigSectionGetter:
    """Proxy around a section."""
    def __init__(self, config, section):
        self.base_config = config
        self.section = section

    def __getitem__(self, key):
        return self.base_config.getstr(f'{self.section}.{key}')
