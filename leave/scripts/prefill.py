import datetime
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


from leave.logalone import isolate
from leave.metadata import LogEntry
from leave.db import (
    CreateLogDBForHash
)


REPO = Path.home() / "btc" / "bitcoin"


@dataclass
class BlockReceived:
    received_size: int = 0
    time_received: Optional[datetime.datetime] = None
    time_reconstructed: Optional[datetime.datetime] = None
    reconstruction_time_ns: float = 0.0

    prefill_count: int = 0
    prefill_size: int = 0
    mempool_count: int = 0
    mempool_size: int = 0
    extra_count: int = 0
    extra_size: int = 0
    missing_count: int = 0
    missing_size: int = 0


@dataclass
class BlockSent:
    block_received: BlockReceived
    peer_id: int
    time_sent: Optional[datetime.datetime] = None
    send_size: int = 0
    tcp_window_size: int = 0


class CBHandler:
    def __init__(self):
        self.total_transaction_rq_count: int = 0
        self.blocks_sent: dict[str, BlockSent] = {}
        self.blocks_received: dict[str, BlockReceived] = {}

    def reco_callback(self, entry: LogEntry, blockhash: str,
                      prefill_count: str, prefill_size: str,
                      mempool_count: str, mempool_size: str,
                      extra_count: str, extra_size: str,
                      missing_count: str, missing_size: str) -> None:
        block = self.blocks_received.get(blockhash, BlockReceived())
        block.time_reconstructed = entry.time()

        block.prefill_count = int(prefill_count)
        block.prefill_size = int(prefill_size)

        block.mempool_count = int(mempool_count)
        block.mempool_size = int(mempool_size)

        block.extra_count = int(extra_count)
        block.extra_size = int(extra_size)

        block.missing_count = int(missing_count)
        block.missing_size = int(missing_size)

        self.blocks_received[blockhash] = block

    # Relies on the assumption that blocks_received == blocks reconstructed,
    # which holds for our observation prefill receiver.
    def blocks_missing_count(self) -> int:
        count = 0
        for _, block in self.blocks_received.items():
            if block.missing_count > 0:
                count += 1
        return count


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage!!!! [script.py] {debug.log} {commit-hash}")
        sys.exit(-1)

    handler = CBHandler()
    # todo, the db should really be an index of db's generating itself based on
    # the logfile, but hmm sometimes commit is unknown in the startup version
    # message...
    db = CreateLogDBForHash(REPO, sys.argv[2])

    # Should it be fuzzy or there be a fuzzy option instead of regex?
    patterns = [
        db.msg_cb(
            search="Successfully reconstructed block",
            callback=handler.reco_callback
        ),
    ]

    isolate(Path(sys.argv[1]), patterns)

    missing = handler.blocks_missing_count()
    total = len(handler.blocks_received)

    success = total - missing

    reco_pct = (success / total) * 100

    print(f"{success}/{total} ({reco_pct:.2f}%) succeeded reconstruction without needing a GETBLOCKTXN roundtrip.")
