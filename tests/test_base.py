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

    def setUp(self):
        super(ConfigGetterTestCase, self).setUp()
        self.example_path = os.path.join(os.path.dirname(__file__), 'example.ini')
        self.example2_path = os.path.join(os.path.dirname(__file__), 'example2.ini')
        self.class_to_test = getconf.ConfigGetter

    def test_no_settings(self):
        """Test when no real settings exist."""
        getter = self.class_to_test('TESTNS')
        self.assertEqual('foo', getter.get('bar', 'foo'))
        self.assertEqual('', getter.get('bar'))
        self.assertEqual((), getter.search_files)
        self.assertEqual((), getter.found_files)

    def test_environ_settings(self):
        """Test fetching key from environment."""
        getter = self.class_to_test('TESTNS')
        with Environ(TESTNS_FOO='blah'):
            self.assertEqual('blah', getter.get('foo', 'foo'))
            self.assertEqual('', getter.get('bar'))

    def test_environ_section(self):
        """Test fetching section.key from environment."""
        getter = self.class_to_test('TESTNS')
        with Environ(TESTNS_FOO_BAR='blah'):
            self.assertEqual('blah', getter.get('foo.bar', 'foo'))
            self.assertEqual('', getter.get('foo.baz'))
            self.assertEqual('', getter.get('foo'))

    def test_nonexistent_file(self):
        """Test fetching from a non-existent config file."""
        getter = self.class_to_test('TESTNS', ['/invalid/path'])
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
        self.assertEqual(('/invalid/path',), getter.search_files)
        self.assertEqual((), getter.found_files)

    def test_real_file(self):
        """Test fetching from the default config file."""
        getter = self.class_to_test('TESTNS', [self.example_path])
        self.assertEqual((self.example_path,), getter.search_files)
        self.assertEqual((self.example_path,), getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key file-defined
            self.assertEqual('13', getter.get('section1.foo'))
            # Same with an int
            self.assertEqual(13, getter.getint('section1.foo'))

    def test_real_file_deprecated_caller(self):
        """Test fetching from the default config file (old syntax)."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            getter = self.class_to_test('TESTNS', self.example_path)
            self.assertTrue("DeprecationWarning" in str(w[0]))

        self.assertEqual((self.example_path,), getter.search_files)
        self.assertEqual((self.example_path,), getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key file-defined
            self.assertEqual('13', getter.get('section1.foo'))
            # Same with an int
            self.assertEqual(13, getter.getint('section1.foo'))

    def test_real_files_as_list(self):
        """Test fetching from several config file, defined as list."""
        getter = self.class_to_test('TESTNS', [self.example_path, self.example2_path])
        self.assertEqual((self.example_path, self.example2_path), getter.search_files)
        self.assertEqual((self.example_path, self.example2_path), getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key file-defined, overridden
            self.assertEqual('24', getter.get('section1.foo'))
            # A section.key defined in the second file
            self.assertEqual('13', getter.get('section2.bar'))
            # A section.key defined in the base file, not overridden
            self.assertEqual('21', getter.get('section1.otherfoo'))

    def test_real_files_as_tuple(self):
        """Test fetching from several config file, defined as tuple."""
        getter = self.class_to_test('TESTNS', (self.example_path, self.example2_path))
        self.assertEqual((self.example_path, self.example2_path), getter.search_files)
        self.assertEqual((self.example_path, self.example2_path), getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key file-defined, overridden
            self.assertEqual('24', getter.get('section1.foo'))
            # A section.key defined in the second file
            self.assertEqual('13', getter.get('section2.bar'))
            # A section.key defined in the base file, not overridden
            self.assertEqual('21', getter.get('section1.otherfoo'))

    def test_real_files_deprecated_caller(self):
        """Test fetching from several config file (old syntax)."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            getter = self.class_to_test('TESTNS', self.example_path, self.example2_path)
            self.assertTrue("DeprecationWarning" in str(w[0]))

        self.assertEqual((self.example_path, self.example2_path), getter.search_files)
        self.assertEqual((self.example_path, self.example2_path), getter.found_files)
        with Environ(TESTNS_FOO='blah'):
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key file-defined, overridden
            self.assertEqual('24', getter.get('section1.foo'))
            # A section.key defined in the second file
            self.assertEqual('13', getter.get('section2.bar'))
            # A section.key defined in the base file, not overridden
            self.assertEqual('21', getter.get('section1.otherfoo'))

    def test_environ_defined_file(self):
        """Test reading from an environment-defined config file."""
        with Environ(TESTNS_CONFIG=self.example_path, TESTNS_FOO='blah'):
            getter = self.class_to_test('TESTNS', [''])
            self.assertEqual((self.example_path,), getter.search_files)
            self.assertEqual((self.example_path,), getter.found_files)
            # A non-file-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless file-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key file-defined
            self.assertEqual('13', getter.get('section1.foo'))

    def test_environ_overrides_config(self):
        """Tests that environment variables take precedence over files."""
        getter = self.class_to_test('TESTNS', [self.example_path])
        self.assertEqual('42', getter.get('bar'))
        self.assertEqual('13', getter.get('section1.foo'))

        with Environ(TESTNS_BAR='blah', TESTNS_SECTION1_FOO='baz'):
            self.assertEqual('blah', getter.get('bar'))
            self.assertEqual('baz', getter.get('section1.foo'))

    def test_getlist_empty(self):
        getter = self.class_to_test('TESTNS', ())
        with Environ(TESTNS_FOO='  ,  ,,,,  '):
            self.assertEqual([], getter.getlist('foo'))

    def test_getlist_single(self):
        getter = self.class_to_test('TESTNS', ())
        with Environ(TESTNS_FOO='foo'):
            self.assertEqual(['foo'], getter.getlist('foo'))

    def test_getlist_multi(self):
        getter = self.class_to_test('TESTNS', ())
        with Environ(TESTNS_FOO='foo,bar,baz'):
            self.assertEqual(['foo', 'bar', 'baz'], getter.getlist('foo'))

    def test_getlist_dirty(self):
        getter = self.class_to_test('TESTNS', ())
        with Environ(TESTNS_FOO='foo,, bar   ,baz   ,,'):
            self.assertEqual(['foo', 'bar', 'baz'], getter.getlist('foo'))

    def test_getlist_nonempty_default(self):
        getter = self.class_to_test('TESTNS', ())
        self.assertEqual(['x', 'foo', 'bar'], getter.getlist('foo', 'x,,foo ,   , bar,,'))

    def test_getbool_empty(self):
        getter = self.class_to_test('TESTNS', ())
        with Environ(TESTNS_FOO=''):
            self.assertFalse(getter.getbool('foo'))

    def test_getbool_true(self):
        getter = self.class_to_test('TESTNS', ())
        with Environ(TESTNS_FOO='on'):
            self.assertTrue(getter.getbool('foo'))

    def test_getbool_badvalue(self):
        getter = self.class_to_test('TESTNS', ())
        with Environ(TESTNS_FOO='bar'):
            self.assertFalse(getter.getbool('foo'))

    def test_getbool_false(self):
        getter = self.class_to_test('TESTNS', ())
        with Environ(TESTNS_FOO='0'):
            self.assertFalse(getter.getbool('foo'))

    def test_getbool_nonempty_default(self):
        getter = self.class_to_test('TESTNS', ())
        self.assertTrue(getter.getbool('foo', 'yes'))

    def test_getint_value(self):
        getter = self.class_to_test('TESTNS', ())
        with Environ(TESTNS_FOO='14'):
            self.assertEqual(14, getter.getint('foo'))

    def test_get_section_env(self):
        getter = self.class_to_test('TESTNS')
        section = getter.get_section('foo')
        with Environ(TESTNS_FOO_BAR='baz'):
            self.assertEqual('baz', section['bar'])

    def test_get_section_file(self):
        getter = self.class_to_test('TESTNS', (self.example_path,))
        section = getter.get_section('section1')
        self.assertEqual('13', section['foo'])

    def test_unicode(self):
        getter = self.class_to_test('TESTNS', (self.example_path,))
        self.assertEqual("Åuŧølīß", getter.get('encoding.noascii'))

        with Environ(TESTNS_ENCODING_NOASCII="ßlūelÿ"):
            self.assertEqual("ßlūelÿ", getter.get('encoding.noascii'))

class DictConfigGetterTestCase(ConfigGetterTestCase):

    def setUp(self):
        super(DictConfigGetterTestCase, self).setUp()
        self.example_dict = {
            'DEFAULT': {
                'bar': '42',
            },
            'section1':{
                'foo': '13',
                'otherfoo': '21',
            },
            'encoding':{
                'noascii': 'Åuŧølīß',
            },
        }

        self.example2_dict = {
            'section1': {
                'foo': '24',
            },
            'section2': {
                'bar': '13',
            },
        }

        self.class_to_test = getconf.DictConfigGetter

    def dict_test_no_settings(self):
        """Test when no real settings exist."""
        getter = self.class_to_test('TESTNS')
        self.assertEqual('foo', getter.get('bar', 'foo'))
        self.assertEqual('', getter.get('bar'))

    def dict_test_environ_settings(self):
        """Test fetching key from environment."""
        getter = self.class_to_test('TESTNS')
        with Environ(TESTNS_FOO='blah'):
            self.assertEqual('blah', getter.get('foo', 'foo'))
            self.assertEqual('', getter.get('bar'))

    def dict_test_environ_section(self):
        """Test fetching section.key from environment."""
        getter = self.class_to_test('TESTNS')
        with Environ(TESTNS_FOO_BAR='blah'):
            self.assertEqual('blah', getter.get('foo.bar', 'foo'))
            self.assertEqual('', getter.get('foo.baz'))
            self.assertEqual('', getter.get('foo'))

    def dict_test_real_dict(self):
        """Test fetching from the default config dict."""
        getter = self.class_to_test('TESTNS', config_dicts=(self.example_dict,))
        with Environ(TESTNS_FOO='blah'):
            # A non-dict-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless dict-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key dict-defined
            self.assertEqual('13', getter.get('section1.foo'))
            # Same with an int
            self.assertEqual(13, getter.getint('section1.foo'))

    def dict_test_real_dicts(self):
        """Test fetching from several config dict."""
        getter = self.class_to_test('TESTNS', config_dicts=(self.example_dict, self.example2_dict))
        with Environ(TESTNS_FOO='blah'):
            # A non-dict-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless dict-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key dict-defined, overridden
            self.assertEqual('24', getter.get('section1.foo'))
            # A section.key defined in the second dict
            self.assertEqual('13', getter.get('section2.bar'))
            # A section.key defined in the base dict, not overridden
            self.assertEqual('21', getter.get('section1.otherfoo'))

    def dict_test_environ_defined_file(self):
        """Test reading from an environment-defined config dict."""
        with Environ(TESTNS_CONFIG=self.example_path, TESTNS_FOO='blah'):
            getter = self.class_to_test('TESTNS', config_dicts=())
            # A non-dict-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless dict-defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key dict-defined
            self.assertEqual('13', getter.get('section1.foo'))

    def dict_test_environ_overrides_dict_config(self):
        """Tests that environment variables take precedence over dicts."""
        getter = self.class_to_test('TESTNS', config_dicts=(self.example_dict,))
        self.assertEqual('42', getter.get('bar'))
        self.assertEqual('13', getter.get('section1.foo'))

    def dict_test_getlist_empty(self):
        getter = self.class_to_test('TESTNS', config_dicts=())
        with Environ(TESTNS_FOO='  ,  ,,,,  '):
            self.assertEqual([], getter.getlist('foo'))

    def dict_test_getlist_single(self):
        getter = self.class_to_test('TESTNS', config_dicts=())
        with Environ(TESTNS_FOO='foo'):
            self.assertEqual(['foo'], getter.getlist('foo'))

    def dict_test_getlist_multi(self):
        getter = self.class_to_test('TESTNS', config_dicts=())
        with Environ(TESTNS_FOO='foo,bar,baz'):
            self.assertEqual(['foo', 'bar', 'baz'], getter.getlist('foo'))

    def dict_test_getlist_dirty(self):
        getter = self.class_to_test('TESTNS', config_dicts=())
        with Environ(TESTNS_FOO='foo,, bar   ,baz   ,,'):
            self.assertEqual(['foo', 'bar', 'baz'], getter.getlist('foo'))

    def dict_test_getlist_nonempty_default(self):
        getter = self.class_to_test('TESTNS', config_dicts=())
        self.assertEqual(['x', 'foo', 'bar'], getter.getlist('foo', 'x,,foo ,   , bar,,'))

    def dict_test_getbool_empty(self):
        getter = self.class_to_test('TESTNS', config_dicts=())
        with Environ(TESTNS_FOO=''):
            self.assertFalse(getter.getbool('foo'))

    def dict_test_getbool_true(self):
        getter = self.class_to_test('TESTNS', config_dicts=())
        with Environ(TESTNS_FOO='on'):
            self.assertTrue(getter.getbool('foo'))

    def dict_test_getbool_badvalue(self):
        getter = self.class_to_test('TESTNS', config_dicts=())
        with Environ(TESTNS_FOO='bar'):
            self.assertFalse(getter.getbool('foo'))

    def dict_test_getbool_false(self):
        getter = self.class_to_test('TESTNS', config_dicts=())
        with Environ(TESTNS_FOO='0'):
            self.assertFalse(getter.getbool('foo'))

    def dict_test_getbool_nonempty_default(self):
        getter = self.class_to_test('TESTNS', config_dicts=())
        self.assertTrue(getter.getbool('foo', 'yes'))

    def dict_test_getint_value(self):
        getter = self.class_to_test('TESTNS', config_dicts=())
        with Environ(TESTNS_FOO='14'):
            self.assertEqual(14, getter.getint('foo'))

    def dict_test_get_section_env(self):
        getter = self.class_to_test('TESTNS')
        section = getter.get_section('foo')
        with Environ(TESTNS_FOO_BAR='baz'):
            self.assertEqual('baz', section['bar'])

    def dict_test_get_section_file(self):
        getter = self.class_to_test('TESTNS', config_dicts=(self.example_dict,))
        section = getter.get_section('section1')
        self.assertEqual('13', section['foo'])

    def dict_test_unicode(self):
        getter = self.class_to_test('TESTNS', config_dicts=(self.example_dict,))
        self.assertEqual("Åuŧølīß", getter.get('encoding.noascii'))

        with Environ(TESTNS_ENCODING_NOASCII="ßlūelÿ"):
            self.assertEqual("ßlūelÿ", getter.get('encoding.noascii'))

    def dict_test_real_dict_and_file(self):
        """Test fetching from a file and a dict."""
        getter = self.class_to_test('TESTNS', config_files=(self.example_path,), config_dicts=(self.example2_dict,))
        with Environ(TESTNS_FOO='blah'):
            # A non-defined value
            self.assertEqual('blah', getter.get('foo', 'foo'))
            # A sectionless defined key
            self.assertEqual('42', getter.get('bar'))
            # A section.key defined, overridden
            self.assertEqual('24', getter.get('section1.foo'))
            # A section.key defined in the dcit
            self.assertEqual('13', getter.get('section2.bar'))
            # A section.key defined in the file, not overridden
            self.assertEqual('21', getter.get('section1.otherfoo'))

    def test_real_files_deprecated_caller(self):
        #DictConfigGetter doesn't support this deprecated action
        pass

    def test_real_file_deprecated_caller(self):
        #DictConfigGetter doesn't support this deprecated action
        pass

if __name__ == '__main__':
    unittest.main()
