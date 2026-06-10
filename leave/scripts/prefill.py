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
    blockhash: Optional[str] = None

    received_size: Optional[int] = 0
    peer_id: Optional[int] = 0
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
    blockhash: Optional[str] = None
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
        self.blocks_sent: list[BlockSent] = []
        self.blocks_received: list[BlockReceived] = []

        self.curr_cb_received: Optional[BlockReceived] = None
        self.curr_cb_sent: Optional[BlockSent] = None

    def blocks_reconstructed(self) -> list[BlockReceived]:
        return [
            block
            for block in self.blocks_received
            if block.time_reconstructed is not None
        ]

    def net_receive_cb(self, entry: LogEntry, msg_type: str,
                       size: str, peer_id: str) -> None:
        if msg_type != "cmpctblock":
            return
        self.curr_cb_received = BlockReceived()
        self.curr_cb_received.received_size = int(size)
        self.curr_cb_received.peer_id = int(peer_id)
        self.curr_cb_received.time_received = entry.time()
        self.blocks_received.append(self.curr_cb_received)

    def init_cb(self, entry: LogEntry, hash: str, size: str) -> None:
        if self.curr_cb_received is None:
            self.curr_cb_received = BlockReceived()
            self.curr_cb_received.received_size = int(size)
            self.blocks_received.append(self.curr_cb_received)
        elif int(size) != self.curr_cb_received.received_size:
            print(
                f"Oops, that's weird, {size} does not match the current CB's"
                f"size of {self.curr_cb_received.received_size}"
            )

        self.curr_cb_received.blockhash = hash

    def reco_cb(self, entry: LogEntry, blockhash: str,
                prefill_count: str, prefill_size: str,
                mempool_count: str, mempool_size: str,
                extra_count: str, extra_size: str,
                missing_count: str, missing_size: str) -> None:
        if self.curr_cb_received is None:
            self.curr_cb_received = BlockReceived()
            self.curr_cb_received.blockhash = blockhash
            self.blocks_received.append(self.curr_cb_received)
        elif self.curr_cb_received.blockhash != blockhash:
            print(
                f"Oops, that's weird, {blockhash} does not match the current CB's"
                f"blockash of {self.curr_cb_received.blockhash}"
            )
        self.curr_cb_received.time_reconstructed = entry.time()

        self.curr_cb_received.prefill_count = int(prefill_count)
        self.curr_cb_received.prefill_size = int(prefill_size)

        self.curr_cb_received.mempool_count = int(mempool_count)
        self.curr_cb_received.mempool_size = int(mempool_size)

        self.curr_cb_received.extra_count = int(extra_count)
        self.curr_cb_received.extra_size = int(extra_size)

        self.curr_cb_received.missing_count = int(missing_count)
        self.curr_cb_received.missing_size = int(missing_size)

    def blocks_missing_count(self) -> int:
        count = 0
        for block in self.blocks_reconstructed():
            if block.missing_count > 0:
                count += 1
        return count

    def prefill_rd_cb(self, entry: LogEntry,
                      redundant_count: str, redundant_size: str,
                      mempool_count: str, mempool_size: str,
                      extrapool_count: str, extrapool_size: str) -> None:
        if self.curr_cb_received is None:
            self.curr_cb_received = BlockReceived()
            self.blocks_received.append(self.curr_cb_received)
        self.curr_cb_received.prefill_rd_count = int(redundant_count)
        self.curr_cb_received.prefill_rd_size = int(redundant_size)
        self.curr_cb_received.prefill_rd_from_mempool_count = int(mempool_count)
        self.curr_cb_received.prefill_rd_from_mempool_size = int(mempool_size)
        self.curr_cb_received.prefill_rd_from_extrapool_count = int(extrapool_count)
        self.curr_cb_received.prefill_rd_from_extrapool_size = int(extrapool_size)

    def tcp_window_cb(self, entry: LogEntry,
                      prefilled_size: str, prefilled_windows_used: str,
                      nonprefilled_size: str, nonprefilled_windows_used: str,
                      window_total: str, window_available: str) -> None:
        if self.curr_cb_sent is None:
            self.curr_cb_sent = BlockSent()
            self.blocks_sent.append(self.curr_cb_sent)
        self.curr_cb_sent.prefilled_cb_size = int(prefilled_size)
        self.curr_cb_sent.prefilled_cb_windows = int(prefilled_windows_used)
        self.curr_cb_sent.nonprefilled_cb_size = int(nonprefilled_size)
        self.curr_cb_sent.nonprefilled_cb_windows = int(nonprefilled_windows_used)
        self.curr_cb_sent.tcp_window_total = int(window_total)
        self.curr_cb_sent.tcp_window_avail = int(window_available)

    def sending_cb(self, entry: LogEntry, is_prefilled: str, size_str: str) -> None:
        size: int = int(size_str)

        if self.curr_cb_sent is None:
            self.curr_cb_sent = BlockSent()
            # not strictly true since this metric usually includes overhead,
            # but close enough and making them equal lets us extract out the
            # blocks that have 0 intended prefill.
            self.curr_cb_sent.prefilled_cb_size = size
            self.curr_cb_sent.nonprefilled_cb_size = size
            self.blocks_sent.append(self.curr_cb_sent)

        if is_prefilled == "prefilled":
            self.curr_cb_sent.prefilled = True
        elif is_prefilled == "not-prefilled":
            self.curr_cb_sent.prefilled = False
        else:
            raise RuntimeError(f"Error processing: {entry.full_line}, unexpected is_prefilled value of `{is_prefilled}`")
        self.curr_cb_sent.send_size = size

    def header_and_ids_cb(self, entry: LogEntry, funcname: str, blockhash: str, peer_id: str) -> None:
        if self.curr_cb_sent is None:
            self.curr_cb_sent = BlockSent()
            self.blocks_sent.append(self.curr_cb_sent)

        self.curr_cb_sent.blockhash = blockhash
        self.curr_cb_sent.peer_id = int(peer_id)
        self.curr_cb_sent.time_sent = entry.time()
        self.curr_cb_sent = None


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

    patterns = [
        # receiving
        (
            "received: %s \\(%u bytes\\)",
            cb_handler.net_receive_cb,
            False,
            "received: cmpctblock",
        ),
        (
            "Initializing PartiallyDownloadedBlock",
            cb_handler.init_cb,
            False,
            "",
        ),
        (
            "Successfully reconstructed block",
            cb_handler.reco_cb,
            False,
            "",
        ),
        (
            ".* txn .* of the prefill were redundant, ",
            cb_handler.prefill_rd_cb,
            False,
            "",
        ),

        # sending
        (
            "Prefilled CB.*TCP windows",
            cb_handler.tcp_window_cb,
            True,
            "",
        ),
        (
            "Sending %s CMPCTBLOCK of size",
            cb_handler.sending_cb,
            True,
            "",
        ),
        (
            "sending header-and-ids",
            cb_handler.header_and_ids_cb,
            False,
            "",
        ),
    ]

    logpatterns = [
        res for search, callback, missing_ok, extra_filter in patterns
        if (res := db.msg_cb(search, callback, missing_ok, extra_filter)) is not None
    ]

    isolate(Path(sys.argv[1]), logpatterns, start_date, end_date)

    blocks_missing_tx = [block for block in cb_handler.blocks_received if block.missing_count > 0]
    total_blocks = len(cb_handler.blocks_reconstructed())

    success = total_blocks - len(blocks_missing_tx)

    reco_pct = (success / total_blocks) * 100

    print(f"{success}/{total_blocks} ({reco_pct:.2f}%) succeeded reconstruction without needing a GETBLOCKTXN roundtrip.")

    prefill_size_total = sum(block.prefill_size for block in cb_handler.blocks_reconstructed())
    prefill_per_block = prefill_size_total / total_blocks

    prefilled_blocks = [block for block in cb_handler.blocks_reconstructed() if block.prefill_count > 1]
    prefilled_block_pct = (len(prefilled_blocks) / total_blocks) * 100

    print(f"{len(prefilled_blocks)}/{total_blocks} ({prefilled_block_pct:.2f}%) of blocks received were prefilled. Average prefill per block received: {prefill_per_block:.1f} bytes.")

    if len(prefilled_blocks) > 0:
        prefilled_and_missing = [block for block in prefilled_blocks if block.missing_count > 0]
        prefilled_and_missing_pct = (len(prefilled_and_missing) / len(prefilled_blocks)) * 100
        print(f"{len(prefilled_and_missing)}/{len(prefilled_blocks)} "
              f"({prefilled_and_missing_pct:.2f}%) of prefilled blocks received "
              f"needed a GETBLOCKTXN roundtrip.")

        prefill_rd_total = sum(block.prefill_rd_size for block in cb_handler.blocks_received)
        redundant_pct = (prefill_rd_total / prefill_size_total) * 100
        redundant_per_block = prefill_rd_total / total_blocks
        print(f"{redundant_pct:.2f}% of bytes received in prefills were redundant.")
        print(f"Avg redundant prefill: {redundant_per_block} bytes/block")

        if (prefill_rd_total):
            prefill_rd_mp_total_size = sum(block.prefill_rd_from_mempool_size for block in cb_handler.blocks_received)
            rd_mp_pct = (prefill_rd_mp_total_size / prefill_rd_total) * 100
            print(f"{rd_mp_pct:.2f}% of redundant prefill bytes already in mempool.")

            prefill_rd_ep_total_size = sum(block.prefill_rd_from_extrapool_size for block in cb_handler.blocks_received)
            rd_ep_pct = (prefill_rd_ep_total_size / prefill_rd_total) * 100
            print(f"{rd_ep_pct:.2f}% of redundant prefill bytes already in extrapool.")

    sent_total_count = len(cb_handler.blocks_sent)
    sent_prefilled = [block for block in cb_handler.blocks_sent if block.prefilled is True]
    if sent_total_count > 0:
        sent_prefilled_pct = (len(sent_prefilled) / sent_total_count) * 100
        print(f"{len(sent_prefilled)}/{sent_total_count} ({sent_prefilled_pct:.2f}%) of blocks sent were prefilled.")


