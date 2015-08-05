getconf
=======

The ``getconf`` project provides simple configuration helpers for Python programs.

It provides a simple API to read from various configuration files and environment variables:

.. code-block:: python

    import getconf
    config = getconf.ConfigGetter('myproj', ['/etc/myproj.conf'])
    db_host = config.get('db.host', 'localhost')
    db_port = config.getint('db.port', 5432)


Beyond this API, getconf aims at unifying configuration setup across development and production systems,
respecting the standard procedures in each system:

* Allow userspace configuration on development systems
* Allow multiple different configurations for continuous integration systems
* Use standard configuration space in ``/etc`` on traditional production servers
* Handle environment-based configuration for cloud-based platforms

``getconf`` supports Python 2.6, 2.7, 3.3, 3.4 and is distributed under the two-clause BSD license.

Links
-----

- Package on `PyPI`_: http://pypi.python.org/pypi/getconf/
- Doc on `ReadTheDocs <http://readthedocs.org/>`_: http://readthedocs.org/docs/getconf/
- Source on `GitHub <http://github.com/>`_: http://github.com/Polyconseil/getconf/


Installation
------------

Intall the package from `PyPI`_, using pip:

.. code-block:: sh

    pip install getconf

Or from GitHub:

.. code-block:: sh

    git clone git://github.com/Polyconseil/getconf


``getconf`` has no external dependancy beyond Python.


Introduction
------------

.. note:: Please refer to the full doc for :doc:`reference <reference>` and
          :doc:`advanced usage <advanced>`.

All configuration values are accessed through the ``getconf.ConfigGetter`` object:

.. code-block:: python

    import getconf
    config = getconf.ConfigGetter('myproj', ['/etc/myproj/settings.ini', './local_settings.ini'])

The above line declares:

* Use the ``myproj`` namespace (explained later; this is mostly used for environment-based configuration, as a prefix for environment variables)
* Look, in turn, at ``/etc/myproj/settings.ini`` (for production) and ``./local_settings.ini`` (for development); the latter overriding the former.


Once the ``getconf.ConfigGetter`` has been configured, it can be used to retrieve settings:

.. code-block:: python

    debug = config.getbool('debug', False)
    db_host = config.get('db.host', 'localhost')
    db_port = config.getint('db.port', 5432)
    allowed_hosts = config.getlist('django.allowed_hosts', ['*'])

All settings have a type (default is text), and accept a default value.
They use namespaces (think 'sections') for easier reading.

With the above setup, ``getconf`` will try to provide ``db.host`` by inspecting
the following options in order (it stops at the first defined value):

- From the environment variable ``MYPROJ_DB_HOST``, if defined
- From the ``host`` key in the ``[db]`` section of ``./local_settings.ini``
- From the ``host`` key in the ``[db]`` section of ``/etc/myproj/settings.ini``
- From the default provided value, ``'localhost'``


Features
--------

**Env-based configuration files**
    An extra configuration file/directory/glob can be provided through ``MYPROJ_CONFIG``;
    it takes precedence over other files

**Default options**
    An extra dictionary can be provided as ``ConfigGetter(defaults=some_dict)``;
    it is used after configuration files and environment variables.

    It should be a dict mapping a section name to a dict of ``key => value``:

    .. code-block:: pycon

        >>> config = ConfigGetter('myproj', defaults={'db': {'host': 'localhost'}})
        >>> config.get('db.host')
        'localhost'

**Typed getters**
    ``getconf`` can convert options into a few standard types:

    .. code-block:: python

        config.getbool('db.enabled', False)
        config.getint('db.port', 5432)
        config.getlist('db.tables')  # Expects a comma-separated list
        config.getfloat('db.auto_vacuum_scale_factor', 0.2)

Concepts
--------

``getconf`` relies on a few key concepts:

**namespace**
    Each ``ConfigGetter`` works within a specific namespace (its first argument).

    Its goal is to avoid mistakes while reading the environment:
    with ``ConfigGetter(namespace='myproj')``, only environment variables
    beginning with ``MYPROJ_`` will be read

**Sections**
    The configuration options for a project often grow quite a lot;
    to restrict complexity, ``getconf`` splits values into sections,
    similar to Python's ``configparser`` module.

    Section are handled differently depending on the actual configuration
    source:

    * ``section.key`` is mapped to ``MYPROJ_SECTION_KEY`` for environment variables
    * ``section.key`` is mapped to ``[section] key =`` in configuration files
    * ``section.key`` is mapped to ``defaults['section']['key']`` in the defaults dict.

**Default section**
    Some settings are actually "globals" for a projet.
    This is handled by unset section names:

    * ``key`` is mapped to ``MYPROJ_KEY`` for environment variables
    * ``key`` is mapped to ``[DEFAULT] key =`` in configuration files
    * ``key`` is mapped to ``defaults['DEFAULT']['key']`` in the defaults dict.


.. _PyPI: http://pypi.python.org/
