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

EXAMPLE_ARG_LIST = [
    "peerid",
    "blockhash",
    "txn_count",
    "txn_size"
]


class TestRegex(unittest.TestCase):
    def test_fmt_to_regex(self):
        print("Test that matching works.")
        r = fmt_to_regex(EXAMPLE_LOG_FMT)
        self.assertRegex(EXAMPLE_LOG_MESSAGE, r)

        print("Test that grouped=true is the default behavior.")
        self.assertEqual(r, fmt_to_regex(EXAMPLE_LOG_FMT, grouped=True))

        print("Test that the right number of groups is present in the pattern.")
        self.assertEqual(r.groups, 4)

        ungrouped_r = fmt_to_regex(EXAMPLE_LOG_FMT, grouped=False)

        print("Test that grouped=true results in 0 groups.")
        self.assertEqual(ungrouped_r.groups, 0)

        print("Test that grouped=false also matches.")
        self.assertRegex(EXAMPLE_LOG_MESSAGE, ungrouped_r)

    def test_regex_add_names(self):
        r = fmt_to_regex(EXAMPLE_LOG_FMT)

        with self.assertRaisesRegex(ValueError, "incorrect length"):
            empty_list = []
            regex_add_names(r.pattern, empty_list)

        with self.assertRaisesRegex(ValueError, "incorrect length"):
            short_list = EXAMPLE_ARG_LIST[:-1]
            regex_add_names(r.pattern, short_list)

        with self.assertRaisesRegex(ValueError, "incorrect length"):
            long_list = EXAMPLE_ARG_LIST + ["extra"]
            regex_add_names(r.pattern, long_list)

        with self.assertRaisesRegex(ValueError, "unique"):
            duplicate_list = EXAMPLE_ARG_LIST[:-1] + ["txn_count"]
            regex_add_names(r.pattern, duplicate_list)

        named_pattern = regex_add_names(r.pattern, EXAMPLE_ARG_LIST)
        match = re.search(named_pattern, EXAMPLE_LOG_MESSAGE)
        self.assertIsNotNone(match.groupdict())
        matchdict = match.groupdict()
        self.assertEqual(matchdict["peerid"], '43')
        self.assertEqual(matchdict["blockhash"], '00000000000000000000793c9c81354b796e2d8e135a6fb583ef6fbc97ff9850')
        self.assertEqual(matchdict["txn_count"], '3083')
        self.assertEqual(matchdict["txn_size"], '1281149')
