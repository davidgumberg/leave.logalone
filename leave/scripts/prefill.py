import sys

from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


from leave.logalone import isolate
from leave.metadata import LogEntry
from leave.db import (
    CreateLogDBForHash
)
from leave.util import parse_datetime


REPO = Path.home() / "btc" / "bitcoin"


@dataclass
class BlockReceived:
    received_size: int = 0
    time_received: Optional[datetime] = None
    time_reconstructed: Optional[datetime] = None
    reconstruction_time_ns: float = 0.0

    prefill_count: int = 0
    prefill_size: int = 0
    mempool_count: int = 0
    mempool_size: int = 0
    extra_count: int = 0
    extra_size: int = 0
    missing_count: int = 0
    missing_size: int = 0

    prefill_rd_count: int = 0
    prefill_rd_size: int = 0
    prefill_rd_from_mempool_count: int = 0
    prefill_rd_from_mempool_size: int = 0
    prefill_rd_from_extrapool_count: int = 0
    prefill_rd_from_extrapool_size: int = 0


@dataclass
class BlockSent:
    block_received: Optional[BlockReceived] = None
    peer_id: Optional[int] = None
    time_sent: Optional[datetime] = None
    send_size: Optional[int] = None

    prefilled: Optional[bool] = None

    prefilled_cb_size: Optional[int] = None
    prefilled_cb_windows: Optional[int] = None
    nonprefilled_cb_size: Optional[int] = None
    nonprefilled_cb_windows: Optional[int] = None

    tcp_window_total: Optional[int] = None
    tcp_window_avail: Optional[int] = None


class CBHandler:
    def __init__(self):
        self.blocks_sent: dict[str, BlockSent] = {}
        self.blocks_received: dict[str, BlockReceived] = {}

        self.current_block_received: Optional[BlockReceived] = None
        self.current_block_sent: Optional[BlockSent] = None

    def reco_cb(self, entry: LogEntry, blockhash: str,
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
        self.current_block_received = self.blocks_received[blockhash]

    # Relies on the assumption that blocks_received == blocks reconstructed,
    # which holds for our observation prefill receiver.
    def blocks_missing_count(self) -> int:
        count = 0
        for _, block in self.blocks_received.items():
            if block.missing_count > 0:
                count += 1
        return count

    def prefill_rd_cb(self, entry: LogEntry,
                      redundant_count: str, redundant_size: str,
                      mempool_count: str, mempool_size: str,
                      extrapool_count: str, extrapool_size: str) -> None:
        if self.current_block_received is None:
            raise RuntimeError(f"Error processing {entry.full_line}\n Somehow current_block_received is None.")
        self.current_block_received.prefill_rd_count = int(redundant_count)
        self.current_block_received.prefill_rd_size = int(redundant_size)
        self.current_block_received.prefill_rd_from_mempool_count = int(mempool_count)
        self.current_block_received.prefill_rd_from_mempool_size = int(mempool_size)
        self.current_block_received.prefill_rd_from_extrapool_count = int(extrapool_count)
        self.current_block_received.prefill_rd_from_extrapool_size = int(extrapool_size)

    def tcp_window_cb(self, entry: LogEntry,
                      prefilled_size: str, prefilled_windows_used: str,
                      nonprefilled_size: str, nonprefilled_windows_used: str,
                      window_total: str, window_available: str) -> None:
        block = BlockSent()
        block.prefilled_cb_size = int(prefilled_size)
        block.prefilled_cb_windows = int(prefilled_windows_used)
        block.nonprefilled_cb_size = int(nonprefilled_size)
        block.nonprefilled_cb_windows = int(nonprefilled_windows_used)
        block.tcp_window_total = int(window_total)
        block.tcp_window_avail = int(window_available)
        self.current_block_sent = block

    def sending_cb(self, entry: LogEntry, is_prefilled: str, size: str) -> None:
        if self.current_block_sent is None:
            raise RuntimeError(f"Error processing: {entry.full_line}, no current_block_sent is set.")

        if is_prefilled == "prefilled":
            self.current_block_sent.prefilled = True
            assert size == self.current_block_sent.prefilled_cb_size
        elif is_prefilled == "not-prefilled":
            self.current_block_sent.prefilled = False
            assert size == self.current_block_sent.nonprefilled_cb_size
        else:
            raise RuntimeError(f"Error processing: {entry.full_line}, unexpected is_prefilled value of `{is_prefilled}`")


if __name__ == "__main__":
    if len(sys.argv) not in [3, 5]:
        print("Usage!!!!")
        print("prefill.py {debug.log} {commit-hash}")
        print("or: prefill.py {debug.log} {commit-hash} {start-date} {end-date}")
        sys.exit(-1)

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    if len(sys.argv) == 5:
        start_date = parse_datetime(sys.argv[3])
        end_date = parse_datetime(sys.argv[4])

    cb_handler = CBHandler()
    # todo, the db should really be an index of db's generating itself based on
    # the logfile, but hmm sometimes commit is unknown in the startup version
    # message...
    db = CreateLogDBForHash(REPO, sys.argv[2])

    # Should it be fuzzy or there be a fuzzy option instead of regex?
    patterns = [
        ("Successfully reconstructed block", cb_handler.reco_cb, False),
        (".* txn .* of the prefill were redundant, ", cb_handler.prefill_rd_cb, False),
        ("Sending %s CMPCTBLOCK of size", cb_handler.sending_cb, True),
    ]

    logpatterns = [
        res for search, callback, missing_ok in patterns
        if (res := db.msg_cb(search, callback, missing_ok)) is not None
    ]

    isolate(Path(sys.argv[1]), logpatterns, start_date, end_date)

    missing = cb_handler.blocks_missing_count()
    total_blocks = len(cb_handler.blocks_received)

    success = total_blocks - missing

    reco_pct = (success / total_blocks) * 100

    print(f"{success}/{total_blocks} ({reco_pct:.2f}%) succeeded reconstruction without needing a GETBLOCKTXN roundtrip.")

    prefill_size_total = sum(block.prefill_size for block in cb_handler.blocks_received.values())
    prefill_per_block = prefill_size_total / total_blocks

    prefilled_block_count = sum(1 for block in cb_handler.blocks_received.values() if block.prefill_size > 1)
    prefilled_block_pct = (prefilled_block_count / total_blocks) * 100

    print(f"{prefilled_block_count}/{total_blocks} ({prefilled_block_pct:.2f}%) of blocks were prefilled. Average prefill per block received: {prefill_per_block} bytes.")

    prefill_rd_total = sum(block.prefill_rd_size for block in cb_handler.blocks_received.values())
    redundant_pct = (prefill_rd_total / prefill_size_total) * 100
    redundant_per_block = prefill_rd_total / total_blocks
    print(f"{redundant_pct:.2f}% of bytes received in prefills were redundant.")
    print(f"Per block avg redundant prefill size: {redundant_per_block} bytes")

    if (prefill_rd_total):
        prefill_rd_mp_total_size = sum(block.prefill_rd_from_mempool_size for block in cb_handler.blocks_received.values())
        rd_mp_pct = (prefill_rd_mp_total_size / prefill_rd_total) * 100
        print(f"{rd_mp_pct:.2f}% of redundant prefill bytes already in mempool.")

        prefill_rd_ep_total_size = sum(block.prefill_rd_from_extrapool_size for block in cb_handler.blocks_received.values())
        rd_ep_pct = (prefill_rd_ep_total_size / prefill_rd_total) * 100
        print(f"{rd_ep_pct:.2f}% of redundant prefill bytes already in extrapool.")

