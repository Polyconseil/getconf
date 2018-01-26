Reference
=========

.. module:: getconf

The ``BaseConfigGetter`` class
------------------------------

.. py:class:: BaseConfigGetter(*config_finders)

    This class works as the base for all ConfigGetters.

    :param config_finders: The list of finders the ``BaseConfigGetter`` will use to lookup keys.
                           Finders are python objects providing the ``find(key)`` method that will be called in
                           the order the ``config_finders`` were provided order until one of them finds the ``key``.
                           The ``find(key)`` method should either return a string or raise ``NotFound`` depending
                           on wheither the ``key`` was found or not.

    .. py:method:: getstr(key[, default=''])

        Retrieve a key from available configuration sources.

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

    .. py:method:: getlist(key[, default=()])

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

    .. py:method:: getbool(key[, default=False])

        Retrieve a key from available configuration sources, and parse it as a boolean.

        The following values are considered as ``True`` : ``'on'``, ``'yes'``, ``'true'``, ``'1'``.
        Case variations of those values also count as ``True``.

    .. py:method:: getint(key[, default=0])

        Retrieve a key from available configuration sources, and parse it as an integer.

    .. py:method:: getfloat(key[, default=0.0])

        Retrieve a key from available configuration sources, and parse it as a floating point number.

    .. py:method:: gettimedelta(key[, default='0d'])

        Retrieve a key from available configuration sources, and parse it as a datetime.timedelta object.


The ``ConfigGetter`` class
---------------------------

.. py:class:: ConfigGetter(namespace, config_files=[config_file_path, ...], defaults={'section':{'key': 'value', ...}, ...})

    A ready-to-use ConfigGetter working working as a proxy around both :attr:`os.environ` and INI configuration files.

    :param str namespace: The namespace for all configuration entry lookups.
                          If an environment variable of ``<NAMESPACE>_CONFIG`` is set, the file at that path
                          will be loaded.
                          Pass in the ``getconf.NO_NAMESPACE`` special value to load an empty namespace.
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

    .. warning:: When running with an empty namespace (``namespace=getconf.NO_NAMESPACE``), the environment variables
                 are looked up under ``<SECTION>_<KEY>`` instead of ``<NAMESPACE>_<SECTION>_<KEY>``; use this setup with
                 care, since getconf might load variables that weren't intended for this application.

    .. warning:: Using dash in section or key would prevent from overriding values using environment variables.
                 Dash are converted to underscore internally, but if you have the same variable using underscore, it would
                 override both of them.

    .. py:method:: get_section(section_name)

        Retrieve a dict-like proxy over a configuration section.
        This is intended to avoid polluting ``settings.py`` with a bunch of
        ``FOO = config.getstr('bar.foo'); BAR = config.getstr('bar.bar')`` commands.

        .. note:: The returned object only supports the ``__getitem__`` side of dicts
                  (e.g. ``section_config['foo']`` will work, ``'foo' in section_config`` won't)

    .. py:method:: get_ini_template()

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


The provided finders
--------------------

.. py:class:: getconf.finders.NamespacedEnvFinder(namespace)

    Keys are lookuped in ``os.environ`` with the provided ``namespace``.
    The ``key`` can follow two formats:

        - ``'foo.bar'``, mapped to section ``'foo'``, key ``'bar'``
        - ``'foo'``, mapped to section ``''``, key ``'bar'``

    The finder will look at ``<NAMESPACE>_<SECTION>_<KEY>`` if ``section`` is set,
    ``<NAMESPACE>_<KEY>`` otherwise.

    Keys are upper-cased and dash are converted to underscore before lookup as using dash in section or key
    would prevent from overriding values using environment variables.

    If the special ``NO_NAMESPACE`` namespace is used, the finder will look at
    ``<SECTION>_<KEY>`` if ``section`` is set, ``<KEY>`` otherwise.

.. py:class:: getconf.finders.MultiINIFilesParserFinder(config_files)

    Keys are lookuped in the provided ``config_files`` using Python's ``ConfigParser``.

    The ``key`` can follow two formats:

        - ``'foo.bar'``, mapped to section ``'foo'``, key ``'bar'``
        - ``'foo'``, mapped to section ``'DEFAULT'``, key ``'bar'``

    The ``config_files`` argument can contain directories and glob that will be expanded
    while preserving the provided order:

        - a directory ``some_dir`` is interpreted as the glob ``some_dir/*``
        - a glob is replaced by the matching files list ordered by name

    Finally, the config parser (which interpolation switched off) will search the ``section.entry``
    value in its files, with the last provided file having the strongest priority.

.. py:class:: getconf.finders.SectionDictFinder(data)

    Keys are lookuped in the provided 1-level nested dictionary ``data``.

    The ``key`` can follow two formats:

        - ``'foo.bar'``, mapped to section ``'foo'``, key ``'bar'``
        - ``'foo'``, mapped to section ``'DEFAULT'``, key ``'bar'``

    The finder will look at ``data[section][key]``.

.. py:class:: getconf.finders.ContentFileFinder(directory, encoding='utf-8')

    Keys are lookuped in the provided directory as files.

    If the directory contains a file named ``key``, its content (decoded as ``encoding``) will
    be returned.

    Typically, this can be used to load configuration from Kubernetes' ConfigMaps and Secrets
    mounted on a volume.


ConfigGetter Example
--------------------

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


BaseConfigGetter example
------------------------

We can easily create a config getter ignoring env varibles.

With the following setup:

.. code-block:: ini

    # /etc/getconf/example.ini
    [DEFAULT]
    env = example

    [db]
    host = foo.example.net

We get:

.. code-block:: python

    # test_config.py
    import getconf
    import getconf.finders
    config = getconf.BaseConfigGetter(
        getconf.finders.MultiINIFilesParserFinder(['/etc/getconf/*.ini']),
        getconf.finders.SectionDictFinder({'db': {'host': 'default.db.host', 'port': '1234'}}),
    )
    config.getstr('env') == 'example'
    config.getstr('db.host') == 'foo.example.net'
    config.getstr('db.port') == '1234'
