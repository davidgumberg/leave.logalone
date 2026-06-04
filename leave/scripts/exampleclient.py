import sys

from pathlib import Path
from leave.logalone import isolate
from leave.metadata import LogEntry
from leave.db import (
    CreateLogDBForHash
)


REPO = Path.home() / "btc" / "bitcoin"


class CBHandler:
    def __init__(self):
        self.total_transaction_rq_count = 0

    def gbt_callback(self, entry: LogEntry, peerid: str, blockhash: str,
                     txn_count: str, txn_size: str) -> None:
        self.total_transaction_rq_count += int(txn_count)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage!!!! [script.py] {debug.log} {commit-hash}")
        sys.exit(-1)

    handler = CBHandler()
    # todo, the db should really be an index of db's generating itself based on the logfile, but hmm sometimes commit is unknown in the startup version message...
    db = CreateLogDBForHash(REPO, sys.argv[2])

    # Should it be fuzzy or there be a fuzzy option instead of regex?
    gbt_pattern = db.msg_cb(
        "Peer.*sent us a GETBLOCKTXN",
        handler.gbt_callback
    )
    isolate(Path(sys.argv[1]), [gbt_pattern])

    print(f"... drumroll please... {handler.total_transaction_rq_count}")
