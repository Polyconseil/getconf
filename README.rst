getconf
=======

The ``getconf`` project provides simple configuration helpers for Python programs.

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

All configuration values are accessed through the ``getconf.ConfigGetter`` object:

.. code-block:: python

    import getconf
    config = getconf.ConfigGetter('fubar', ['/etc/fubar/settings.ini', './local_settings.ini'])

The above line declares:

* Use the ``fubar`` namespace (mostly used for environment-based configuration, as a prefix for environment variables)
* Look, in turn, at ``/etc/fubar/settings.ini`` (for production) and ``./local_settings.ini`` (for development); the latter overriding the former.


Once the ``getconf.ConfigGetter`` has been configured, it can be used to retrieve settings:

.. code-block:: python

    debug = config.getbool('debug', False)
    db_host = config.get('db.host')
    db_port = config.getint('db.port', 5432)
    allowed_hosts = config.getlist('django.allowed_hosts', ['*'])

All settings have a type (default is text), and accept a default value.
They use namespaces (think 'sections') for easier reading.

With the above setup, ``getconf`` will try to provide ``db.host`` by inspecting
the following options in order (it stops at the first defined value):

- From the environment variable ``FUBAR_DB_HOST``, if defined
- If a ``FUBAR_CONFIG`` environment variable is defined, from the ``host`` key of the ``[db]`` section of that file
- From the ``host`` key in the ``[db]`` section of ``./local_settings.ini``
- From the ``host`` key in the ``[db]`` section of ``/etc/fubar/settings.ini``
- From the default provided value


Recommanded layout
------------------

Managing configuration can quickly turn into hell; here are a few guidelines:

* Choose where default values are stored
* Define how complex system-wide setup may get
* Decide whether local, development configuration is needed
* And whether user-local overrides are relevant

======================= =============== =============================== =================== =============== ========================
Use case                Example program Defaults storage                System-wide         Path-based      User-based
======================= =============== =============================== =================== =============== ========================
End-user binary         screen, bash    Within the code                 Optional            No              Yes
Folder-based soft       git, hg, ...    Within the code                 Optional            Yes             Yes (global settings)
System daemon           uwsgi, ...      Default file with package       Yes                 No              No
Webapp                  sentry, ...     Within the code                 Yes                 Yes (for dev)   No
======================= =============== =============================== =================== =============== ========================

This would lead to:

- End-user binary:  ``ConfigGetter('vim', ['/etc/vimrc', '~/.vimrc'])``
- Folder-based (git): ``ConfigGetter('git', ['/etc/gitconfig', '~/.git/config', './.git/config'])``
- System daemon: ``ConfigGetter('uwsgi', ['/usr/share/uwsgi/defaults.ini', '/etc/uwsgi/conf.d'])``
- Webapp: ``ConfigGetter('sentry', ['/etc/sentry/conf.d/', './dev_settings.ini'], defaults=sentry_defaults)``


.. _PyPI: http://pypi.python.org/
