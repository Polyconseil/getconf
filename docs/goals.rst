Goals
=====

``getconf`` aims to solve a specific problem: provide a simple way to load settings in a platform-typical manner.


The problem
-----------

Daemons and centralized applications need to fetch some platform-specific configuration to run:

* Mode of operation (debug vs. production vs. packaging)
* Address of remote services (databases, other servers, ...)
* Credentials

Beyond those required settings, an application needs to configure its behavior (timeouts, retries, languages, ...).


Various solutions exist:

* Command line flags
* Environment variables
* Files in ``/etc``


The approach
------------

``getconf`` has been designed to provide the following features:

Readability:
  * All options can be defined in a single file
  * The provided values are typechecked (``int``, ``float``, ...)
  * All settings can have a default

Development:
  * If I checkout the code and execute my program's entry point, it should be able to start
  * If my local setup is slightly different from the default (non-standard DB port, ...),
    I just have to put a simple ``local_settings.ini`` file in the current directory

Continuous integration:
  The continuous integration server just needs to set a few well-defined environment variables
  to point the program to the test databases, servers, ...

Production:
  * In a could-like setup, I can use facilities provided by my platform to set the appropriate environment variables
  * In a simpler, dedicated server setup, the application can also be configured with files in ``/etc``



Other options
-------------

While desiging ``getconf``, we looked at other options:

Define everything in files
    * This makes it difficult to override a single setting (where should the file be?)
    * Not compatible with env-based cloud platforms
    * dev and prod often have very different configurations, but flat files don't provide a simple switch to set those defaults

Define everything in the environment
    Requires a prod-like setup for starting local servers, with files listing the environment variables

Load a single file, which ``includes`` others
    * Quickly turns into a maze of "local includes dev includes base"
    * Hard to see where a setting is defined
