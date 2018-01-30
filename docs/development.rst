Development
===========

Clone the repository and install the development dependencies in a virtualenv:

.. code-block:: sh

    pip install -r requirements_dev.txt

To run tests:

.. code-block:: sh

    nosetests

To make a release, use the ``release`` target:

.. code-block:: sh

    make release

which relies on `zest.releaser`_.


.. _zest.releaser: https://zestreleaser.readthedocs.io/en/latest/index.html
