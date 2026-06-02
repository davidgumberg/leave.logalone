import sys

from pathlib import Path
from leave.logpattern import leavelog
from leave.metadata import LogEntry
from leave.db import (
    CreateLogDBForHash
)


REPO = Path.home() / "btc" / "bitcoin"


class CBHandler:
    def __init__(self):
        self.total_transaction_rq_count = 0

    def gbt_callback(self, _: LogEntry, dict: dict) -> None:
        self.total_transaction_rq_count += int(dict["txn_count"])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage!!!! [script.py] {debug.log} {commit-hash}")
        sys.exit(-1)

    handler = CBHandler()
    # todo, the db should really be an index of db's generating itself based on the logfile, but hmm sometimes commit is unknown in the startup version message...
    db = CreateLogDBForHash(REPO, sys.argv[2])

    # Should it be fuzzy or there be a fuzzy option instead of regex?
    gbt_pattern = db.msg_with_args(
        "Peer.*sent us a GETBLOCKTXN",
        [
            "peerid", "blockhash", "txn_count", "txn_size"
        ],
        handler.gbt_callback
    )
    leavelog(Path(sys.argv[1]), [gbt_pattern])

    print(f"... drumroll please... {handler.total_transaction_rq_count}")
