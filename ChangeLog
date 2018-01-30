ChangeLog
=========

1.8.0 (2018-01-30)
------------------

*New:*

    * Add ``BaseConfigGetter`` and the notion of "finders" to ease customization.

*Note:*

    * Python 2.7 and 3.3 support will be dropped in next minor version.

1.7.1 (2017-10-20)
------------------

*Bugfix:*

    * Allows to override a configuration containing a dash.


1.7.0 (2017-02-23)
------------------

*New:*

    * Allow using an empty namespace
      (``ConfigGetter(namespace=getconf.NO_NAMESPACE``) to load unprefixed
      environment variables.

1.6.0 (2017-02-03)
------------------

*New:*

    * Remove support for string interpolation in .ini file
      If this undocumented getconf feature is still needed by some users,
      we might consider restoring it in a future release.

1.5.2 (2017-01-23)
------------------

*New:*

    * Add a new gettimedelta function to parse simple durations expressed as
      strings (10 days as '10d', 3 hours as '3h', etc.)


1.5.1 (2016-12-15)
------------------

*New:*

    * Display the key of the value that triggers an error to help resolve.


1.5.0 (2016-05-11)
------------------

*New:*

    * Better AssertionError messages when default values have the wrong type.
    * Add ConfigGetter.get_ini_template() method


1.4.1 (2015-08-28)
------------------

*New:*

    * Improve error reporting when raising on wrongly typed defaults

1.4.0 (2015-08-27)
------------------

*New:*

    * Enforce type checking on every getconf.getXXX() call
    * Add getconf.getstr() method
    * Enable using None as default value for every function
    * Better support for Python 3.3, 3.4 and wheel distribution

*Deprecated:*

    * Use of strings as default values for getconf.getlist()
    * Use of getconf.get() in favor of getconf.getstr()

1.3.0 (2015-04-14)
------------------

*New:*

    * Add getfloat() method
    * Allow globs in `config_files`
    * <PROJECT>_CONFIG env var will now have the same behaviour than `config_files` items


1.2.1 (2014-10-24)
------------------

*Bugfix:*

    * Fix version number

1.2.0 (2014-10-20)
------------------

*New:*

    * Add support for directory-based configuration and providing defaults through a dict

*Removed:*

    * Remove support for ``ConfigGetter(namespace, file1, file2, file3)`` syntax (deprecated in 1.1.0),
      use ``ConfigGetter(namespace, [file1, file2, file3])`` instead

1.1.0 (2014-08-18)
------------------

*New:*

    * New initialization syntax

*Deprecated*

    * Using argument list for config file paths when initializing ConfigGetter is now deprecated,
      you need to use a list (use `ConfigGetter(namespace, ['settings_1.ini', 'settings_2.ini'])` instead of
      `ConfigGetter(namespace, 'settings_1.ini', 'settings_2.ini')`)


1.0.1 (2014-04-13)
------------------

*Bugfix:*

    * Fix packaging (missing requirements files)

1.0.0 (2014-04-12)
------------------

*New:*

    * First version

.. vim:et:ts=4:sw=4:tw=79:ft=rst:
