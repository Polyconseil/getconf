Reference
=========

.. module:: getconf


The ``ConfigGetter`` class
---------------------------

.. class:: ConfigGetter(namespace, config_files=[config_file_path, ...], defaults={'section':{'key': 'value', ...}, ...})

    This class works as a proxy around both :attr:`os.environ` and INI configuration files.

    :param str namespace: The namespace for all configuration entry lookups.
                          If an environment variable of ``<NAMESPACE>_CONFIG`` is set, the file at that path
                          will be loaded.
    :param list config_files: List of ini-style configuration files to use.
                              Each item may either be the path to a simple file, or to a directory
                              (if the path ends with a '/') or a glob pattern (which will select all the files
                              matching the pattern according to the rules used by the shell).
                              Each directory path will be replaced by the list of
                              its directly contained files, in alphabetical order, excluding those whose name
                              starts with a '.'.
                              Provided configuration files are read in the order their name was provided,
                              each overriding the next ones' values. ``<NAMESPACE>_CONFIG`` takes precedence over
                              all ``config_files`` contents.
    :param dict defaults: Dictionary of defaults values that are fetch with the lowest priority.
                          The value for 'section.key' will be looked up at ``defaults['section']['key']``.

    .. method:: getstr(key[, default=''])

        Retrieve a key from available environments.

        :param str key: The name of the field to use.
        :param str default: The default value (string) for the field; optional

        .. note:: The ``key`` param accepts two formats:

                  - ``'foo.bar'``, mapped to section ``'foo'``, key ``'bar'``
                  - ``'foo'``, mapped to section ``''``, key ``'bar'``

        This looks, in order, at:

        - ``<NAMESPACE>_<SECTION>_<KEY>`` if ``section`` is set, ``<NAMESPACE>_<KEY>`` otherwise
        - The ``<key>`` entry of the ``<section>`` section of the file given in ``<NAMESPACE>_CONFIG``
        - The ``<key>`` entry of the ``<section>`` section of each file given in ``config_files``
        - The ``default`` value

    .. method:: getlist(key[, default=()])

        Retrieve a key from available configuration sources, and parse it as a list.

        .. warning::

            The default value has the same syntax as expected values, e.g ``foo,bar,baz``.
            It is **not** a list.

        It splits the value on commas, and return stripped non-empty values:

        .. code-block:: pycon

            >>> os.environ['A'] = 'foo'
            >>> os.environ['B'] = 'foo,bar, baz,,'
            >>> getter.getlist('a')
            ['foo']
            >>> getter.getlist('b')
            ['foo', 'bar', 'baz']

    .. method:: getbool(key[, default=False])

        Retrieve a key from available configuration sources, and parse it as a boolean.

        The following values are considered as ``True`` : ``'on'``, ``'yes'``, ``'true'``, ``'1'``.
        Case variations of those values also count as ``True``.

    .. method:: getint(key[, default=0])

        Retrieve a key from available configuration sources, and parse it as an integer.

    .. method:: getfloat(key[, default=0.0])

        Retrieve a key from available configuration sources, and parse it as a floating point number.

    .. method:: get_section(section_name)

        Retrieve a dict-like proxy over a configuration section.
        This is intended to avoid polluting ``settings.py`` with a bunch of
        ``FOO = config.get('bar.foo'); BAR = config.get('bar.bar')`` commands.

        .. note:: The returned object only supports the ``__getitem__`` side of dicts
                  (e.g. ``section_config['foo']`` will work, ``'foo' in section_config`` won't)

    .. method:: get_ini_template()

        Return INI like commented content equivalent to the default values.

        For example:

        .. code-block:: pycon

            >>> getter.getlist('section.bar', default=['a', 'b'])
            ['a', 'b']
            >>> getter.getbool('foo', default=True, doc="Set foo to True to enable the Truth")
            True
            >>> print(g.get_ini_template())
            [DEFAULT]
            ; NAMESPACE_FOO - type=bool - Set foo to True to enable the Truth
            ;foo = on

            [section]
            ; NAMESPACE_SECTION_BAR - type=list
            ;bar = a, b

        .. note:: This template is generated based on the `getxxxx` calls performed on the
                  ConfigGetter. If some calls are optional, the corresponding options might
                  not be present in the `get_ini_template` return value.


Example
-------

With the following setup:

.. code-block:: python

    # test_config.py
    import getconf
    config = getconf.ConfigGetter('getconf', ['/etc/getconf/example.ini'])

    print("Env: %s" % config.getstr('env', 'dev'))
    print("DB: %s" % config.getstr('db.host', 'localhost'))
    print("Debug: %s" % config.getbool('dev.debug', False))

.. code-block:: ini

    # /etc/getconf/example.ini
    [DEFAULT]
    env = example

    [db]
    host = foo.example.net

.. code-block:: ini

    # /etc/getconf/production.ini
    [DEFAULT]
    env = prod

    [db]
    host = prod.example.net


We get the following outputs:

.. code-block:: sh

    # Default setup
    $ python test_config.py
    Env: example
    DB: foo.example.net
    Debug: False

    # Override 'env'
    $ GETCONF_ENV=alt python test_config.py
    Env: alt
    DB: foo.example.net
    Debug: False

    # Override 'dev.debug'
    $ GETCONF_DEV_DEBUG=on python test_config.py
    Env: example
    DB: foo.example.net
    Debug: True

    # Read from an alternate configuration file
    $ GETCONF_CONFIG=/etc/getconf/production.ini python test_config.py
    Env: prod
    DB: prod.example.net
    Debug: False

    # Mix it up
    $ GETCONF_DEV_DEBUG=on GETCONF_CONFIG=/etc/getconf/production python test_config.py
    Env: prod
    DB: prod.example.net
    Debug: True
