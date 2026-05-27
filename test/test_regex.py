import unittest
import re

from leave.regex import (
    fmt_to_regex,
    regex_add_names
)

# Todo: add a few more patterns

# Important test case that this ends in a newline!
EXAMPLE_LOG_FMT = "Peer %d sent us a GETBLOCKTXN for block %s, sending a BLOCKTXN with %u txns. (%u bytes)\n"
EXAMPLE_LOG_MESSAGE = "2026-01-07T15:41:31.606100Z [cmpctblock] Peer 43 sent us a GETBLOCKTXN for block 00000000000000000000793c9c81354b796e2d8e135a6fb583ef6fbc97ff9850, sending a BLOCKTXN with 3083 txns. (1281149 bytes)"


class TestRegex(unittest.TestCase):
    def test_fmt_to_regex(self):
        r = fmt_to_regex(EXAMPLE_LOG_FMT)
        self.assertRegex(EXAMPLE_LOG_MESSAGE, r)

    def test_regex_add_names(self):
        r = fmt_to_regex(EXAMPLE_LOG_FMT)

        arg_list = [
            "peerid",
            "blockhash",
            "txn_count",
            "txn_size"
        ]

        with self.assertRaisesRegex(ValueError, "incorrect length"):
            empty_list = []
            regex_add_names(r.pattern, empty_list)

        with self.assertRaisesRegex(ValueError, "incorrect length"):
            short_list = arg_list[:-1]
            regex_add_names(r.pattern, short_list)

        with self.assertRaisesRegex(ValueError, "incorrect length"):
            long_list = arg_list + ["extra"]
            regex_add_names(r.pattern, long_list)

        with self.assertRaisesRegex(ValueError, "unique"):
            duplicate_list = arg_list[:-1] + ["txn_count"]
            regex_add_names(r.pattern, duplicate_list)

        named_pattern = regex_add_names(r.pattern, arg_list)
        match = re.search(named_pattern, EXAMPLE_LOG_MESSAGE)
        print(named_pattern)
        self.assertIsNotNone(match)
        matchdict = match.groupdict()
        self.assertEqual(matchdict["peerid"], '43')
        self.assertEqual(matchdict["blockhash"], '00000000000000000000793c9c81354b796e2d8e135a6fb583ef6fbc97ff9850')
        self.assertEqual(matchdict["txn_count"], '3083')
        self.assertEqual(matchdict["txn_size"], '1281149')
