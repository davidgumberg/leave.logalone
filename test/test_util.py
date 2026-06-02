from re import escape
import unittest

from leave.util import (
    string_from_literals,
)


class TestStringUtils(unittest.TestCase):
    def test_join_string_literals(self):
        literal1 = r"String literal! \n"
        single_literal = f"\"{literal1}\""
        self.assertEqual(string_from_literals(single_literal), literal1)

        literal2 = "Do it again!"
        multi_literal = f"\"{literal1}\" \"{literal2}\""
        expected=f"{literal1}{literal2}"
        self.assertEqual(string_from_literals(multi_literal), expected)

        broken_multi_literal = f"\"{literal1}\" message between! forbideeen \"{literal2}\""
        with self.assertRaisesRegex(ValueError, "non whitespace characters"):
            string_from_literals(broken_multi_literal)

        escaped_quotes_message = r'Unknown inv type \"%s\" received from peer=%d\n'
        print(escaped_quotes_message)
        escaped_quotes_literal = f"\"{escaped_quotes_message}\""
        self.assertEqual(string_from_literals(escaped_quotes_literal), escaped_quotes_message)
