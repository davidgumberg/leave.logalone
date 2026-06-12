import sys

from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from statistics import median, mean
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

    prefill_desired: Optional[bool] = None
    prefilled_cb_size: Optional[int] = None
    prefilled_cb_windows: Optional[int] = None
    nonprefilled_cb_size: Optional[int] = None
    nonprefilled_cb_windows: Optional[int] = None

    tcp_window_total: Optional[int] = None
    tcp_window_avail: Optional[int] = None

    @property
    def prefill_size(self) -> Optional[int]:
        if (
            self.prefilled_cb_size is not None and
            self.nonprefilled_cb_size is not None
        ):
            return self.prefilled_cb_size - self.nonprefilled_cb_size
        return None


class ReceiveHandler:
    def __init__(self):
        self.blocks_received: list[BlockReceived] = []
        self.curr_cb_received: Optional[BlockReceived] = None

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
                f"blockhash of {self.curr_cb_received.blockhash}"
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


class SendHandler:
    def __init__(self):
        self.blocks_sent: list[BlockSent] = []
        self.curr_cb_sent: Optional[BlockSent] = None

    def tcp_window_cb(self, entry: LogEntry,
                      prefilled_size: str, prefilled_windows_used: str,
                      nonprefilled_size: str, nonprefilled_windows_used: str,
                      window_total: str, window_available: str) -> None:
        if self.curr_cb_sent is None:
            self.curr_cb_sent = BlockSent()
            self.blocks_sent.append(self.curr_cb_sent)

        # This is a hack that exploits the fact that in current code this
        # message is only logged when prefill is desired.
        self.curr_cb_sent.prefill_desired = True
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
            # not strictly true since this metric usually includes overhead
            self.curr_cb_sent.prefilled_cb_size = size
            self.curr_cb_sent.nonprefilled_cb_size = size
            self.curr_cb_sent.prefill_desired = False
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

    receive_handler = ReceiveHandler()
    send_handler = SendHandler()
    # todo, the db should really be an index of db's generating itself based on
    # the logfile, but hmm sometimes commit is unknown in the startup version
    # message...
    db = CreateLogDBForHash(REPO, sys.argv[2])

    patterns = [
        # receiving
        (
            "received: %s \\(%u bytes\\)",
            receive_handler.net_receive_cb,
            False,
            "received: cmpctblock",
        ),
        (
            "Initializing PartiallyDownloadedBlock",
            receive_handler.init_cb,
            False,
            "",
        ),
        (
            "Successfully reconstructed block",
            receive_handler.reco_cb,
            False,
            "",
        ),
        (
            ".* txn .* of the prefill were redundant, ",
            receive_handler.prefill_rd_cb,
            False,
            "",
        ),

        # sending
        (
            "Prefilled CB.*TCP windows",
            send_handler.tcp_window_cb,
            True,
            "",
        ),
        (
            "Sending %s CMPCTBLOCK of size",
            send_handler.sending_cb,
            True,
            "",
        ),
        (
            "sending header-and-ids",
            send_handler.header_and_ids_cb,
            False,
            "",
        ),
    ]

    logpatterns = [
        res for search, callback, missing_ok, extra_filter in patterns
        if (res := db.msg_cb(search, callback, missing_ok, extra_filter)) is not None
    ]

    isolate(Path(sys.argv[1]), logpatterns, start_date, end_date)

    blocks_missing_tx = [block for block in receive_handler.blocks_received if block.missing_count > 0]
    total_blocks = len(receive_handler.blocks_reconstructed())

    success = total_blocks - len(blocks_missing_tx)

    reco_pct = (success / total_blocks) * 100

    print(f"{success}/{total_blocks} ({reco_pct:.2f}%) succeeded "
          f"reconstruction without needing a GETBLOCKTXN roundtrip.")

    prefill_size_total = sum(block.prefill_size for block in receive_handler.blocks_reconstructed())
    prefill_per_block = prefill_size_total / total_blocks

    received_prefilled_blocks = [block for block in receive_handler.blocks_reconstructed() if block.prefill_count > 1]
    prefilled_block_pct = (len(received_prefilled_blocks) / total_blocks) * 100

    print(f"{len(received_prefilled_blocks)}/{total_blocks} "
          f"({prefilled_block_pct:.2f}%) of blocks received were prefilled with "
          f"more than just the coinbase. Mean prefill received (incl. "
          f"coinbase): {prefill_per_block:.1f} bytes / block.")

    if len(received_prefilled_blocks) > 0:
        prefilled_and_missing = [block for block in received_prefilled_blocks if block.missing_count > 0]
        prefilled_and_missing_pct = (len(prefilled_and_missing) / len(received_prefilled_blocks)) * 100
        print(f"{len(prefilled_and_missing)}/{len(received_prefilled_blocks)} "
              f"({prefilled_and_missing_pct:.2f}%) of prefilled blocks received "
              f"needed a GETBLOCKTXN roundtrip.")

        prefill_rd_total = sum(block.prefill_rd_size for block in receive_handler.blocks_received)
        redundant_pct = (prefill_rd_total / prefill_size_total) * 100
        redundant_per_block = prefill_rd_total / total_blocks
        print(f"{redundant_pct:.2f}% of bytes received in prefills were redundant.")
        print(f"Mean redundant prefill: {redundant_per_block:.2f} bytes/block")

        if (prefill_rd_total):
            prefill_rd_mp_total_size = sum(block.prefill_rd_from_mempool_size for block in receive_handler.blocks_received)
            rd_mp_pct = (prefill_rd_mp_total_size / prefill_rd_total) * 100
            print(f"{rd_mp_pct:.2f}% of redundant prefill bytes already in mempool.")

            prefill_rd_ep_total_size = sum(block.prefill_rd_from_extrapool_size for block in receive_handler.blocks_received)
            rd_ep_pct = (prefill_rd_ep_total_size / prefill_rd_total) * 100
            print(f"{rd_ep_pct:.2f}% of redundant prefill bytes already in extrapool.")

    sent_total_count = len(send_handler.blocks_sent)
    sent_prefilled = [block for block in send_handler.blocks_sent if block.prefilled is True]
    if sent_total_count > 0:
        sent_prefilled_pct = (len(sent_prefilled) / sent_total_count) * 100
        print(f"{len(sent_prefilled)}/{sent_total_count} ({sent_prefilled_pct:.2f}%) of all blocks sent were prefilled.")
        prefill_desired = [
            sent for sent in send_handler.blocks_sent
            if sent.prefill_desired is True
        ]
        prefill_not_desired = [
            sent for sent in send_handler.blocks_sent
            if sent.prefill_desired is not None and sent.prefill_desired is False
        ]
        prefill_not_applicable = [
            sent for sent in send_handler.blocks_sent
            if sent.prefill_desired is None
        ]
        prefill_not_desired_pct = (len(prefill_not_desired) / sent_total_count) * 100
        print(f"{len(prefill_not_desired)} / {sent_total_count} "
              f"({prefill_not_desired_pct:.2f}%) of blocks sent had no prefill "
              f"desired.")

        prefill_desired_pct = (len(prefill_desired) / sent_total_count) * 100
        print(f"{len(prefill_desired)} / {sent_total_count} "
              f"({prefill_desired_pct:.2f}%) of blocks sent had a prefill "
              f"desired.")

        prefill_na_pct = (len(prefill_not_applicable) / sent_total_count) * 100
        print(f"{len(prefill_not_applicable)} / {sent_total_count} "
              f"({prefill_na_pct:.2f}%) of blocks sent prefilling was not "
              f"applicable. (blocks below tip)")

        prefill_desired_sent_pct = (len(sent_prefilled) / len(prefill_desired))
        print(f"{len(sent_prefilled)} / {len(prefill_desired)} "
              f"({prefill_desired_sent_pct:.2f}%) of blocks where prefill was"
              f"desired it was also sent.")

        prefill_avail = [sent.tcp_window_avail for sent in sent_prefilled if sent.tcp_window_avail is not None]
        print(f"TCP Window available bytes; median: {median(prefill_avail):.0f}, mean: {mean(prefill_avail):.2f}")
        prefill_size = [sent.prefill_size for sent in sent_prefilled if sent.prefill_size is not None]
        print(f"Prefill size in bytes; median: {median(prefill_size):.0f}, mean: {mean(prefill_size):.2f}")
