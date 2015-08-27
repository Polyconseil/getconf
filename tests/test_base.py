#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2015 Polyconseil SAS.
# This code is distributed under the two-clause BSD License.

from __future__ import unicode_literals

import os
import sys
import unittest
import warnings

import getconf


class Environ(object):
    def __init__(self, **kwargs):
        self.old = {}
        self.override = kwargs

    def __enter__(self):
        for k, v in self.override.items():
            if k in os.environ:
                self.old[k] = os.environ[k]
            if sys.version_info[0] == 2:
                v = v.encode('utf-8')  # os.environ is bytes in PY2
            os.environ[k] = v

    def __exit__(self, *args, **kwargs):
        for k in self.override:
            if k in self.old:
                os.environ[k] = self.old[k]
            else:
                del os.environ[k]


class ConfigGetterTestCase(unittest.TestCase):
    example_directory = os.path.join(os.path.dirname(__file__), 'config/')
    example_path = os.path.join(example_directory, 'example.ini')
    example2_path = os.path.join(example_directory, 'example2.ini')

    def test_no_settings(self):
        """Test when no real settings exist."""
        getter = getconf.ConfigGetter('TESTNS')
        self.assertEqual('foo', getter.getstr('bar', 'foo'))
        self.assertEqual('', getter.getstr('bar'))
        self.assertEqual([], getter.search_files)
        self.assertEqual([], getter.found_files)

    def test_environ_settings(self):
        """Test fetching key from environment."""
        getter = getconf.ConfigGetter('TESTNS')
        with Environ(TESTNS_FOO='blah'):
            self.assertEqual('blah', getter.getstr('foo', 'foo'))
            self.assertEqual('', getter.getstr('bar'))

    def test_environ_section(self):
        """Test fetching section.key from environment."""
        getter = getconf.ConfigGetter('TESTNS')
        with Environ(TESTNS_FOO_BAR='blah'):
            self.assertEqual('blah', getter.getstr('foo.bar', 'foo'))
            self.assertEqual('', getter.getstr('foo.baz'))
            self.assertEqual('', getter.getstr('foo'))

    def test_nonexistent_file(self):
        """Test fetching from a non-existent config file."""
        getter = getconf.ConfigGetter('TESTNS', ['/invalid/path'])
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.getstr('foo', 'foo'))
        self.assertEqual(['/invalid/path'], getter.search_files)
        self.assertEqual([], getter.found_files)

    def test_real_file(self):
        """Test fetching from the default config file."""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path])
        self.assertEqual([self.example_path], getter.search_files)
        self.assertEqual([self.example_path], getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.getstr('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.getstr('bar'))
            # A section.key file-defined
            self.assertEqual('13', getter.getstr('section1.foo'))
            # Same with an int
            self.assertEqual(13, getter.getint('section1.foo'))

    def test_real_files(self):
        """Test fetching from several config file."""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path, self.example2_path])
        self.assertEqual([self.example_path, self.example2_path], getter.search_files)
        self.assertEqual([self.example_path, self.example2_path], getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.getstr('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.getstr('bar'))
            # A section.key file-defined in example and example2 => example2 wins
            self.assertEqual('24', getter.getstr('section1.foo'))
            # A section.key defined in the second file only
            self.assertEqual('13', getter.getstr('section2.bar'))
            # A section.key defined in the base file, not overridden
            self.assertEqual('21', getter.getstr('section1.otherfoo'))

    def test_from_directory(self):
        """Test fetching from a directory."""
        getter = getconf.ConfigGetter('TESTNS', config_files=[self.example_directory])
        self.assertEqual([os.path.join(self.example_directory, '*')], getter.search_files)
        self.assertEqual([self.example_path, self.example2_path], getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.getstr('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.getstr('bar'))
            # A section.key file-defined in both => example2 wins
            self.assertEqual('24', getter.getstr('section1.foo'))
            # A section.key defined in the second file only
            self.assertEqual('13', getter.getstr('section2.bar'))
            # A section.key defined in the base file, not overridden
            self.assertEqual('21', getter.getstr('section1.otherfoo'))

    def test_from_directory_and_files(self):
        """Test fetching from both directories and files"""
        getter = getconf.ConfigGetter('TESTNS', [self.example_directory, self.example_path])
        self.assertEqual([os.path.join(self.example_directory, '*'), self.example_path], getter.search_files)
        self.assertEqual([self.example_path, self.example2_path, self.example_path], getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.getstr('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.getstr('bar'))
            # A section.key file-defined in all three => example wins
            self.assertEqual('13', getter.getstr('section1.foo'))
            # A section.key defined in the second file
            self.assertEqual('13', getter.getstr('section2.bar'))
            # A section.key defined in the base file, not overridden
            self.assertEqual('21', getter.getstr('section1.otherfoo'))

    def test_from_globs(self):
        """Test fetching from globs"""
        getter = getconf.ConfigGetter('TESTNS', [os.path.join(self.example_directory, '*2.ini')])
        self.assertEqual([os.path.join(self.example_directory, '*2.ini')], getter.search_files)
        self.assertEqual([self.example2_path], getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.getstr('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('', getter.getstr('bar'))
            # A section.key file-defined in all three => example wins
            self.assertEqual('24', getter.getstr('section1.foo'))
            # A section.key defined in the second file
            self.assertEqual('13', getter.getstr('section2.bar'))
            # A section.key defined in the base file, not overridden
            self.assertEqual('', getter.getstr('section1.otherfoo'))

    def test_environ_defined_globs(self):
        """Test reading from an environment-defined config globs"""
        with Environ(TESTNS_CONFIG=os.path.join(self.example_directory, '*2.ini'), TESTNS_FOO='blah'):
            getter = getconf.ConfigGetter('TESTNS', [])
            self.assertEqual([os.path.join(self.example_directory, '*2.ini')], getter.search_files)
            self.assertEqual([self.example2_path], getter.found_files)
            # A non-file-defined value
            self.assertEqual('blah', getter.getstr('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('', getter.getstr('bar'))
            # A section.key file-defined
            self.assertEqual('24', getter.getstr('section1.foo'))

    def test_environ_defined_file(self):
        """Test reading from an environment-defined config file."""
        with Environ(TESTNS_CONFIG=self.example_path, TESTNS_FOO='blah'):
            getter = getconf.ConfigGetter('TESTNS', [])
            self.assertEqual([self.example_path], getter.search_files)
            self.assertEqual([self.example_path], getter.found_files)
            # A non-file-defined value
            self.assertEqual('blah', getter.getstr('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.getstr('bar'))
            # A section.key file-defined
            self.assertEqual('13', getter.getstr('section1.foo'))

    def test_environ_overrides_config(self):
        """Tests that environment variables take precedence over files."""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path])
        self.assertEqual('42', getter.getstr('bar'))
        self.assertEqual('13', getter.getstr('section1.foo'))

        with Environ(TESTNS_BAR='blah', TESTNS_SECTION1_FOO='baz'):
            self.assertEqual('blah', getter.getstr('bar'))
            self.assertEqual('baz', getter.getstr('section1.foo'))

    def test_get_defaults_dict(self):
        """Test fetching from the default config dict with non-string values."""
        warnings.warn("Use of get() directly is deprecated. Use .getstr() instead", DeprecationWarning)
        getter = getconf.ConfigGetter('TESTNS', defaults={'DEFAULT':{"test":'54'}})
        self.assertEqual('54', getter.get('test'))
        self.assertEqual('54', getter.getstr('test'))
        self.assertEqual(54, getter.getint('test'))
        self.assertEqual(54.0, getter.getfloat('test'))
        self.assertEqual(False, getter.getbool('test'))
        self.assertEqual(['54', ], getter.getlist('test'))

    def test_get_defaults(self):
        """Test fetching from the default config dict."""
        warnings.warn("Use of get() directly is deprecated. Use .getstr() instead", DeprecationWarning)
        getter = getconf.ConfigGetter('TESTNS')
        self.assertEqual('', getter.get('test'))
        self.assertEqual('foo', getter.get('test', 'foo'))
        self.assertEqual(None, getter.get('test', None))

    def test_get_defaults_raises(self):
        """Test fetching from the default config dict with non-string values."""
        warnings.warn("Use of get() directly is deprecated. Use .getstr() instead", DeprecationWarning)
        getter = getconf.ConfigGetter('TESTNS', defaults={'DEFAULT':{"test":'54'}})
        self.assertRaises(AssertionError, lambda: getter.get('test', False))
        self.assertRaises(AssertionError, lambda: getter.get('test', 42))
        self.assertRaises(AssertionError, lambda: getter.get('test', 4.2))
        self.assertRaises(AssertionError, lambda: getter.get('test', (1, )))

    def test_getstr_defaults(self):
        """Test fetching from the default config dict."""
        getter = getconf.ConfigGetter('TESTNS')
        self.assertEqual('', getter.getstr('test'))
        self.assertEqual('foo', getter.getstr('test', 'foo'))
        self.assertEqual(None, getter.getstr('test', None))

    def test_getstr_defaults_raises(self):
        """Test fetching from the default config dict with non-string values."""
        getter = getconf.ConfigGetter('TESTNS')
        self.assertRaises(AssertionError, lambda: getter.getstr('test', False))
        self.assertRaises(AssertionError, lambda: getter.getstr('test', 42))
        self.assertRaises(AssertionError, lambda: getter.getstr('test', 4.2))
        self.assertRaises(AssertionError, lambda: getter.getstr('test', (1, )))

    def test_getlist_empty(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='  ,  ,,,,  '):
            self.assertEqual([], getter.getlist('foo'))

    def test_getlist_single(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='foo'):
            self.assertEqual(['foo'], getter.getlist('foo'))

    def test_getlist_multi(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='foo,bar,baz'):
            self.assertEqual(['foo', 'bar', 'baz'], getter.getlist('foo'))

    def test_getlist_dirty(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='foo,, bar   ,baz   ,,'):
            self.assertEqual(['foo', 'bar', 'baz'], getter.getlist('foo'))

    def test_getlist_nonempty_default(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        self.assertEqual(['x', 'foo', 'bar'], getter.getlist('foo', 'x,,foo ,   , bar,,'))
        self.assertEqual(['x', 'foo', 'bar'], getter.getlist('foo', ['x', 'foo', 'bar']))
        self.assertEqual(['x', 'foo', 'bar'], getter.getlist('foo', ('x', 'foo', 'bar')))

    def test_getlist_defaults(self):
        """Test fetching the defaults in every possible way"""
        getter = getconf.ConfigGetter('TESTNS')
        self.assertEqual([], getter.getlist('test'))
        self.assertEqual(None, getter.getlist('test', None))

    def test_getlist_defaults_raises(self):
        """Test fetching from the default config dict with non-list or string values."""
        getter = getconf.ConfigGetter('TESTNS')
        self.assertRaises(AssertionError, lambda: getter.getlist('test', False))
        self.assertRaises(AssertionError, lambda: getter.getlist('test', 42))
        self.assertRaises(AssertionError, lambda: getter.getlist('test', 4.2))

    def test_getbool_empty(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO=''):
            self.assertFalse(getter.getbool('foo'))

    def test_getbool_true(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='on'):
            self.assertTrue(getter.getbool('foo'))

    def test_getbool_badvalue(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='bar'):
            self.assertFalse(getter.getbool('foo'))

    def test_getbool_false(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='0'):
            self.assertFalse(getter.getbool('foo'))

    def test_getbool_defaults(self):
        """Test fetching the default in every possible way"""
        getter = getconf.ConfigGetter('TESTNS')
        self.assertEqual(False, getter.getbool('test'))
        self.assertTrue(getter.getbool('foo', True))
        self.assertEqual(None, getter.getbool('test', None))

    def test_getbool_defaults_raises(self):
        """Test fetching from the default config dict with non-bool values."""
        getter = getconf.ConfigGetter('TESTNS')
        self.assertRaises(AssertionError, lambda: getter.getbool('test', 'False'))
        self.assertRaises(AssertionError, lambda: getter.getbool('test', 42))
        self.assertRaises(AssertionError, lambda: getter.getbool('test', 4.2))
        self.assertRaises(AssertionError, lambda: getter.getbool('test', (1, )))

    def test_getint_value(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='14'):
            self.assertEqual(14, getter.getint('foo'))

    def test_getint_defaults(self):
        """Test fetching the default in every possible way"""
        getter = getconf.ConfigGetter('TESTNS')
        self.assertEqual(0, getter.getint('test'))
        self.assertEqual(42, getter.getint('foo', 42))
        self.assertEqual(None, getter.getint('test', None))

    def test_getint_defaults_raises(self):
        """Test fetching from the default config dict with non-int values."""
        getter = getconf.ConfigGetter('TESTNS')
        self.assertRaises(AssertionError, lambda: getter.getint('test', '42'))
        self.assertRaises(AssertionError, lambda: getter.getint('test', 4.2))
        self.assertRaises(AssertionError, lambda: getter.getint('test', (1, )))

    def test_getfloat_value(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='42'):
            value = getter.getfloat('foo')
            self.assertEqual(42, value)
            self.assertEqual(42.0, value)

        with Environ(TESTNS_FOO='42.3'):
            self.assertEqual(42.3, getter.getfloat('foo'))

    def test_getfloat_empty_value(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO=''):
            self.assertRaises(ValueError, getter.getfloat, 'foo')

    def test_getfloat_bad_value(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='a'):
            self.assertRaises(ValueError, getter.getfloat, 'foo')

    def test_getfloat_bad_format(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='1,2'):
            self.assertRaises(ValueError, getter.getfloat, 'foo')

    def test_getfloat_defaults(self):
        """Test fetching the default in every possible way"""
        getter = getconf.ConfigGetter('TESTNS')
        self.assertEqual(0.0, getter.getfloat('test'))
        self.assertEqual(42.3, getter.getfloat('foo', 42.3))
        self.assertEqual(None, getter.getfloat('test', None))

    def test_getfloat_defaults_raises(self):
        """Test fetching from the default config dict with non-float values."""
        getter = getconf.ConfigGetter('TESTNS')
        self.assertRaises(AssertionError, lambda: getter.getfloat('test', False))
        self.assertRaises(AssertionError, lambda: getter.getfloat('test', 42))
        self.assertRaises(AssertionError, lambda: getter.getfloat('test', '4.2'))
        self.assertRaises(AssertionError, lambda: getter.getfloat('test', (1, )))

    def test_get_section_env(self):
        getter = getconf.ConfigGetter('TESTNS')
        section = getter.get_section('foo')
        with Environ(TESTNS_FOO_BAR='baz'):
            self.assertEqual('baz', section['bar'])

    def test_get_section_file(self):
        getter = getconf.ConfigGetter('TESTNS', [self.example_path])
        section = getter.get_section('section1')
        self.assertEqual('13', section['foo'])

    def test_unicode(self):
        getter = getconf.ConfigGetter('TESTNS', [self.example_path])
        self.assertEqual("Åuŧølīß", getter.getstr('encoding.noascii'))

        with Environ(TESTNS_ENCODING_NOASCII="ßlūelÿ"):
            self.assertEqual("ßlūelÿ", getter.getstr('encoding.noascii'))

    def test_sub_section(self):
        """Test fetching a two dimension dict."""
        getter = getconf.ConfigGetter('TESTNS', defaults={'DEFAULT':{"test":'54'}, 'section1':{'key': '88'}})
        self.assertEqual('88', getter.getstr('section1.key', 'foo'))

    def test_defaults_with_file(self):
        """Test fetching from default and file without named arguments"""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path], defaults={'DEFAULT':{"test":'54'}})
        self.assertEqual('54', getter.getstr('test', 'foo'))
        self.assertEqual('13', getter.getstr('section1.foo', 'foo'))

    def test_defaults_with_directory(self):
        """Test fetching from default and file without named arguments"""
        getter = getconf.ConfigGetter('TESTNS',
            config_files=[self.example_directory],
            defaults={'DEFAULT':{"test":'54'}, 'section1':{'otherfoo':'yes'}},
        )
        self.assertEqual('54', getter.getstr('test', 'foo'))
        self.assertEqual('24', getter.getstr('section1.foo', 'foo'))
        self.assertEqual('21', getter.getstr('section1.otherfoo', 'no'))

    def test_named_arguments(self):
        """Test fetching from default and file with named arguments"""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path], defaults={'DEFAULT':{"test":'54'}})
        self.assertEqual('54', getter.getstr('test', 'foo'))
        self.assertEqual('13', getter.getstr('section1.foo', 'foo'))

    def test_file_overide_default(self):
        """Test that default dict is overridden by file"""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path],
            defaults={'DEFAULT':{"test":'54'}, 'section1':{'foo': '72'}})
        self.assertEqual('13', getter.getstr('section1.foo', 'foo'))

    def test_environ_overrides_default(self):
        """Test that default dict is overridden by environment"""
        getter = getconf.ConfigGetter('TESTNS', defaults={'DEFAULT':{"test":'54'}, 'section1':{'foo': '72'}})
        with Environ(TESTNS_SECTION1_FOO='blah'):
            self.assertEqual('blah', getter.getstr('section1.foo'))


if __name__ == '__main__':
    unittest.main()
