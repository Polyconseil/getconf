Advanced use
============

getconf supports some more complex setups; this document describes advanced options.


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


Defaults
--------

The default value may be provided in three different ways:

Upon access
    Use the ``default`` parameter of getters: ``config.getstr('db.host', default='localhost')``

    This is pretty handy when all configuration values are read once and stored in another object.
    However, if the ``ConfigGetter`` object is the reference "configuration-holder" object, repeating
    the default at each call is a sure way to get mismatches between various code sections.


Using a ``defaults`` directory
    The constructor for ``ConfigGetter`` takes an extra keyword argument, ``defaults``, that is used
    after all provided configuration files:

    .. code-block:: python

        import getconf
        config = getconf.ConfigGetter('myproj', ['~/.myproj.ini', '/etc/myproj.ini'], defaults={'logging': {'target': 'stderr'}})

    With the above setup, ``config.getstr('logging.target')`` will be set to ``'stderr'`` if no value is provided through
    the environment nor the configuration files.


In a package-owned configuration file
    For complex projects, the list of settings can get huge.
    In those cases, it may be useful to provide a default configuration file alongside the package,
    with each option documented.

    This default configuration file can also be used as a default, reference file:

    .. code-block:: python

        import os
        import getconf

        # If we're in mymod/cli.py, config is at mymod/config/defaults.ini
        filepath = os.path.abspath(__file__)
        default_config = os.path.join(os.path.dirname(filepath), 'config', 'defaults.ini')
        config = getconf.ConfigGetter('mymod', [default_config, '/etc/mymod.ini', '~/.mymod.ini'])

    With the above setup, the package-provided ``defaults.ini`` will be used as defaults.

    .. note:: Don't forget to include the ``defaults.ini`` file in your package,
              with ``setup.py``'s ``include_package_data=True`` and ``MANIFEST.ini``'s
              ``include mymod/config/defaults.ini``.


Configuration files in a folder
-------------------------------

For complex production projects, a common pattern is to split configuration among
several files -- for instance, a standard file holds logging settings,
a platform-dependent one provides standard system paths, an infrastructure-related one
has all server host/port pairs, and a secured one contains the passwords.

In order to support this pattern, ``getconf``'s ``config_files`` list accepts
folders as well; they are automatically detected on startup (using ``os.path.isdir``).

With the following layout:

.. code-block:: sh

    /etc
    └── myproj
        ├── .keepdir
        ├── 01_logging.ini
        └── 02_passwords.ini

Just setup your getter with ``config = getconf.ConfigGetter('myproj', ['/etc/myproj/', '~/.config/myproj.ini'])``;
this is strictly equivalent to using ``config = getconf.ConfigGetter('myproj', ['01_logging.ini', '02_passwords.ini', '~/.config/myproj.ini'])``.

.. note:: Remember: ``ConfigGetter`` parses configuration files in order
          this means that files provided at the beginning of the list are overridden by the next ones.

          This aligns with the natural alphabetical handling of files:
          when using a folder, we want definitions from ``99_overrides`` to override those in ``00_base``.


Precedency
----------

When reading configuration from multiple sources, it can be complex to determine which source overrides which.

``getconf``'s precedence rules should be natural and easy to understand:

- Environment variables **ALWAYS** override other sources
- Configuration files are parsed in the order they are declared (last declaration wins)
- global defaults (in ``ConfigGetter(defaults={})``) come before calling-defaults (in ``config.getstr('x.y', default='blah')``), which come last.

Two special cases need to be handled:

- The environment-provided configuration file (``<NAMESPACE>_CONFIG``) has precedency over configuration files declared in ``ConfigGetter(config_files=[])``
- When a configuration file is actually a directory (even if provided through ``<NAMESPACE>_CONFIG``),
  its directly contained files are inserted in **ALPHABETICAL ORDER**, so that ``99_foo``
  actually overrides ``10_base``.

Example
"""""""

.. note:: This example is an extremely complex layout, for illustration purposes.
          Understanding it might hurt your head. Please prefer simpler layouts!

With the following layout:

.. code-block:: sh

    /etc
    ├── myproj.conf
    ├── myproj
    │   ├── .keepdir
    │   ├── 10_logging.ini
    │   └── 20_passwords.ini
    └── myproj.local
        ├── .keepdir
        ├── 15_logging.ini
        └── 20_passwords.ini

And the following environment variables:

.. code-block:: sh

    MYPROJ_CONFIG=/etc/myproj.local
    MYPROJ_DB_HOST=localhost

And this ``ConfigGetter`` setup:

.. code-block:: python

    import getconf
    config = getconf.ConfigGetter('myproj', ['/etc/myproj.conf', '/etc/myproj'], defaults={'db': {'host': 'remote', 'port': '5432'}})


Then:

- ``config.getstr('db.host')`` is read from ``MYPROJ_DB_HOST=localhost``
- ``config.getstr('db.name', 'foo')`` looks, in turn:

  - At ``/etc/myproj.local/20_passwords.ini``'s ``[db] name =``
  - At ``/etc/myproj.local/15_logging.ini``'s ``[db] name =``
  - At ``/etc/myproj/20_passwords.ini``'s ``[db] name =``
  - At ``/etc/myproj/10_logging.ini``'s ``[db] name =``
  - At ``/etc/myproj.conf``'s ``[db] name =``
  - Defaults to ``foo``

- ``config.getstr('db.port', '1234')`` looks, in turn:

  - At ``/etc/myproj.local/20_passwords.ini``'s ``[db] port =``
  - At ``/etc/myproj.local/15_logging.ini``'s ``[db] port =``
  - At ``/etc/myproj/20_passwords.ini``'s ``[db] port =``
  - At ``/etc/myproj/10_logging.ini``'s ``[db] port =``
  - At ``/etc/myproj.conf``'s ``[db] port =``
  - Defaults to ``defaults['db']['port'] = '5432'``


.. _PyPI: http://pypi.python.org/
