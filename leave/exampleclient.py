import sys

from pathlib import Path

from leave.commands import rg_filter
from leave.metadata import LogEntry

from leave.db import (
    CreateLogDBForHash
)


REPO = Path.home() / "btc" / "bitcoin"
HASH = "83df64d7491b"


class CBHandler:
    def __init__(self):
        self.total_transaction_rq_count = 0

    def gbt_callback(self, _: LogEntry, dict: dict) -> None:
        self.total_transaction_rq_count += dict["txn_count"]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage!!!!")
        sys.exit(-1)

    handler = CBHandler()
    # todo, the db should really be an index of db's generating itself based on the logfile.
    db = CreateLogDBForHash(REPO, HASH)

    # LogDebug(BCLog::CMPCTBLOCK, "Peer %d sent us a GETBLOCKTXN for block %s, sending a BLOCKTXN with %u txns. (%u bytes)\n", pfrom.GetId(), block.GetHash().ToString(), resp.txn.size(), tx_requested_size);
    # Should it be fuzzy or there be a fuzzy option instead of regex?
    gbt_pattern = db.msg_with_args(
        "Peer.*sent us a GETBLOCKTXN",
        [
            "peerid", "blockhash", "txn_count", "txn_size"
        ],
        handler.gbt_callback
    )
    print(gbt_pattern.regex_nocapture)
    filter_patterns: list[str] = [gbt_pattern.regex_nocapture]

    filtered_lines = rg_filter(filter_patterns, Path(sys.argv[1]))
    print(filtered_lines)
