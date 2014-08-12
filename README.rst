getconf
=======

The ``getconf`` project provides simple configuration helpers for Python project.

It aims at unifying configuration setup across development and production systems,
respecting the standard procedures in each system:

* Allow userspace configuration on development systems
* Allow multiple different configurations for continuous integration systems
* Use standard configuration space in ``/etc`` on traditional production servers
* Handle environment-based configuration for cloud-based platforms

``getconf`` supports Python 2.6, 2.7, 3.3, and is distributed under the two-clause BSD licence.

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

    $ git clone git://github.com/Polyconseil/getconf

Introduction
------------

All configuration values are accessed through ``getconf.ConfigGetter`` object:

.. code-block:: python

    import getconf
    config = getconf.ConfigGetter('fubar', ['/etc/fubar/settings.ini', './local_settings.ini'])

The above line declares:

* Use the ``fubar`` namespace (mostly used for environment-based configuration, as a prefix for environment variables)
* Look, in turn, at ``/etc/fubar/settings.ini`` (for production) and ``./local_settings.ini`` (for development)


Once the ``getconf.ConfigGetter`` has been configured, it can be used to retrieve settings:

.. code-block:: python

    debug = config.getbool('debug', False)
    db_host = config.get('db.host')
    db_port = config.getint('db.port', 5432)
    allowed_hosts = config.getlist('django.allowed_hosts', ['*'])

All settings have a type (default is text), and accept a default value.
They use namespaces for easier reading.

With the above setup, ``getconf`` will try to provide ``db.host`` by inspecting
the following options in order (it stops at the first defined value):

- From the environment variable ``FUBAR_DB_HOST``, if defined
- If a ``FUBAR_CONFIG`` environment variable is defined, from the ``host`` key of the ``[db]`` section of that file
- From the ``host`` key in the ``[db]`` section of ``./local_settings.ini``
- From the ``host`` key in the ``[db]`` section of ``/etc/fubar/settings.ini``
- From the default provided value

.. _PyPI: http://pypi.python.org/
