import unittest

from leave.regex import (
    fmt_to_regex
)

EXAMPLE_LOG_FMT = "Peer %d sent us a GETBLOCKTXN for block %s, sending a BLOCKTXN with %u txns. (%u bytes)\n"
EXAMPLE_LOG_MESSAGE = "2026-01-07T15:41:31.606100Z [cmpctblock] Peer 43 sent us a GETBLOCKTXN for block 00000000000000000000793c9c81354b796e2d8e135a6fb583ef6fbc97ff9850, sending a BLOCKTXN with 3083 txns. (1281149 bytes)"


class TestFmtToRegex(unittest.TestCase):
    def test_succeeds(self):
        pattern = fmt_to_regex(EXAMPLE_LOG_FMT)
        self.assertRegex(EXAMPLE_LOG_MESSAGE, pattern)
