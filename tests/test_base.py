#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2014 Polyconseil SAS.
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
        self.assertEqual('foo', getter.get('bar', 'foo'))
        self.assertEqual('', getter.get('bar'))
        self.assertEqual([], getter.search_files)
        self.assertEqual([], getter.found_files)

    def test_environ_settings(self):
        """Test fetching key from environment."""
        getter = getconf.ConfigGetter('TESTNS')
        with Environ(TESTNS_FOO='blah'):
            self.assertEqual('blah', getter.get('foo', 'foo'))
            self.assertEqual('', getter.get('bar'))

    def test_environ_section(self):
        """Test fetching section.key from environment."""
        getter = getconf.ConfigGetter('TESTNS')
        with Environ(TESTNS_FOO_BAR='blah'):
            self.assertEqual('blah', getter.get('foo.bar', 'foo'))
            self.assertEqual('', getter.get('foo.baz'))
            self.assertEqual('', getter.get('foo'))

    def test_nonexistent_file(self):
        """Test fetching from a non-existent config file."""
        getter = getconf.ConfigGetter('TESTNS', ['/invalid/path'])
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
        self.assertEqual(['/invalid/path'], getter.search_files)
        self.assertEqual([], getter.found_files)

    def test_real_file(self):
        """Test fetching from the default config file."""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path])
        self.assertEqual([self.example_path], getter.search_files)
        self.assertEqual([self.example_path], getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key file-defined
            self.assertEqual('13', getter.get('section1.foo'))
            # Same with an int
            self.assertEqual(13, getter.getint('section1.foo'))

    def test_real_files(self):
        """Test fetching from several config file."""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path, self.example2_path])
        self.assertEqual([self.example_path, self.example2_path], getter.search_files)
        self.assertEqual([self.example_path, self.example2_path], getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key file-defined in example and example2 => example2 wins
            self.assertEqual('24', getter.get('section1.foo'))
            # A section.key defined in the second file only
            self.assertEqual('13', getter.get('section2.bar'))
            # A section.key defined in the base file, not overridden
            self.assertEqual('21', getter.get('section1.otherfoo'))

    def test_from_directory(self):
        """Test fetching from a directory."""
        getter = getconf.ConfigGetter('TESTNS', config_files=[self.example_directory])
        self.assertEqual([self.example_path, self.example2_path], getter.search_files)
        self.assertEqual([self.example_path, self.example2_path], getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key file-defined in both => example2 wins
            self.assertEqual('24', getter.get('section1.foo'))
            # A section.key defined in the second file only
            self.assertEqual('13', getter.get('section2.bar'))
            # A section.key defined in the base file, not overridden
            self.assertEqual('21', getter.get('section1.otherfoo'))

    def test_from_directory_and_files(self):
        """Test fetching from both directories and files"""
        getter = getconf.ConfigGetter('TESTNS', [self.example_directory, self.example_path])
        self.assertEqual([self.example_path, self.example2_path, self.example_path], getter.search_files)
        self.assertEqual([self.example_path, self.example2_path, self.example_path], getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key file-defined in all three => example wins
            self.assertEqual('13', getter.get('section1.foo'))
            # A section.key defined in the second file
            self.assertEqual('13', getter.get('section2.bar'))
            # A section.key defined in the base file, not overridden
            self.assertEqual('21', getter.get('section1.otherfoo'))

    def test_environ_defined_file(self):
        """Test reading from an environment-defined config file."""
        with Environ(TESTNS_CONFIG=self.example_path, TESTNS_FOO='blah'):
            getter = getconf.ConfigGetter('TESTNS', [])
            self.assertEqual([self.example_path], getter.search_files)
            self.assertEqual([self.example_path], getter.found_files)
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key file-defined
            self.assertEqual('13', getter.get('section1.foo'))

    def test_environ_overrides_config(self):
        """Tests that environment variables take precedence over files."""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path])
        self.assertEqual('42', getter.get('bar'))
        self.assertEqual('13', getter.get('section1.foo'))

        with Environ(TESTNS_BAR='blah', TESTNS_SECTION1_FOO='baz'):
            self.assertEqual('blah', getter.get('bar'))
            self.assertEqual('baz', getter.get('section1.foo'))

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

    def test_getbool_nonempty_default(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        self.assertTrue(getter.getbool('foo', 'yes'))

    def test_getint_value(self):
        getter = getconf.ConfigGetter('TESTNS', [])
        with Environ(TESTNS_FOO='14'):
            self.assertEqual(14, getter.getint('foo'))

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
        self.assertEqual("Åuŧølīß", getter.get('encoding.noascii'))

        with Environ(TESTNS_ENCODING_NOASCII="ßlūelÿ"):
            self.assertEqual("ßlūelÿ", getter.get('encoding.noascii'))

    def test_defaults(self):
        """Test fetching from the default config dict."""
        getter = getconf.ConfigGetter('TESTNS', defaults={'DEFAULT':{"test":'54'}})
        self.assertEqual('54', getter.get('test', 'foo'))

    def test_sub_section(self):
        """Test fetching a two dimension dict."""
        getter = getconf.ConfigGetter('TESTNS', defaults={'DEFAULT':{"test":'54'}, 'section1':{'key': '88'}})
        self.assertEqual('88', getter.get('section1.key', 'foo'))

    def test_defaults_with_file(self):
        """Test fetching from default and file without named arguments"""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path], defaults={'DEFAULT':{"test":'54'}})
        self.assertEqual('54', getter.get('test', 'foo'))
        self.assertEqual('13', getter.get('section1.foo', 'foo'))

    def test_defaults_with_directory(self):
        """Test fetching from default and file without named arguments"""
        getter = getconf.ConfigGetter('TESTNS',
            config_files=[self.example_directory],
            defaults={'DEFAULT':{"test":'54'}, 'section1':{'otherfoo':'yes'}},
        )
        self.assertEqual('54', getter.get('test', 'foo'))
        self.assertEqual('24', getter.get('section1.foo', 'foo'))
        self.assertEqual('21', getter.get('section1.otherfoo', 'no'))

    def test_named_arguments(self):
        """Test fetching from default and file with named arguments"""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path], defaults={'DEFAULT':{"test":'54'}})
        self.assertEqual('54', getter.get('test', 'foo'))
        self.assertEqual('13', getter.get('section1.foo', 'foo'))

    def test_file_overide_default(self):
        """Test that default dict is overridden by file"""
        getter = getconf.ConfigGetter('TESTNS', [self.example_path],
            defaults={'DEFAULT':{"test":'54'}, 'section1':{'foo': '72'}})
        self.assertEqual('13', getter.get('section1.foo', 'foo'))

    def test_environ_overrides_default(self):
        """Test that default dict is overridden by environment"""
        getter = getconf.ConfigGetter('TESTNS', defaults={'DEFAULT':{"test":'54'}, 'section1':{'foo': '72'}})
        with Environ(TESTNS_SECTION1_FOO='blah'):
            self.assertEqual('blah', getter.get('section1.foo'))


if __name__ == '__main__':
    unittest.main()
