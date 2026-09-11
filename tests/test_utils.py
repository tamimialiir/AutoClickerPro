"""
Unit tests for utility functions, key parsing, and updater version parsing.
"""

import unittest
from utils import parse_key_combo, str_to_key, SPECIAL_KEYS
from updater import parse_version

class TestUtils(unittest.TestCase):
    def test_parse_key_combo(self):
        mods, main = parse_key_combo("ctrl+c")
        self.assertEqual(len(mods), 1)
        self.assertEqual(main, "c")

        mods, main = parse_key_combo("ctrl+alt+delete")
        self.assertEqual(len(mods), 2)
        self.assertEqual(main, "delete")

        mods, main = parse_key_combo("F1")
        self.assertEqual(len(mods), 0)
        self.assertEqual(main, "f1")

    def test_parse_version(self):
        self.assertEqual(parse_version("v5.2"), (5, 2))
        self.assertEqual(parse_version("v6.0.1"), (6, 0, 1))
        self.assertTrue(parse_version("v6.0") > parse_version("v5.2"))
        self.assertTrue(parse_version("v5.2.1") > parse_version("v5.2"))
        self.assertFalse(parse_version("v5.1") > parse_version("v5.2"))

if __name__ == "__main__":
    unittest.main()
