# -*- coding: utf-8 -*-
# Copyright (c) 2011-2014 Polyconseil SAS.
# This code is distributed under the two-clause BSD License.
"""Compatibility primitives for Python2.6->Python3.3."""


import logging
import sys


if sys.version_info[:2] <= (2, 6):
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

else:
    from logging import NullHandler


if sys.version_info[0] == 2:
    PY2 = True
    text_type = unicode
    import ConfigParser as configparser
else:
    PY2 = False
    text_type = str
    import configparser
