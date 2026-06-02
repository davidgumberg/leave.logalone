import unittest

from leave.util import (
    string_from_literals,
)


class TestStringUtils(unittest.TestCase):
    def test_join_string_literals(self):
        literal1 = "String literal!"
        single_literal = f"\"{literal1}\""
        self.assertEqual(string_from_literals(single_literal), literal1)

        literal2 = "Do it again!"
        multi_literal = f"\"{literal1}\" \"{literal2}\""
        expected=f"{literal1}{literal2}"
        self.assertEqual(string_from_literals(multi_literal), expected)

        broken_multi_literal = f"\"{literal1}\" message between! forbideeen \"{literal2}\""
        with self.assertRaisesRegex(ValueError, "non whitespace characters"):
            string_from_literals(broken_multi_literal)
