import os
import subprocess
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch


from leave.commands import (
    commit_exists,
    is_git_folder,
    rg_filter
)


class TestGitCommands(unittest.TestCase):
    def test_is_git_folder(self):
        with tempfile.TemporaryDirectory() as topdir:
            # Tell git to not chdir into this dir. Who knows, the tmpdir might
            # be in a git repo!
            # https://git-scm.com/docs/git#Documentation/git.txt-GITCEILINGDIRECTORIES
            with patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": topdir}):
                # make a child directory
                subdir = Path(topdir) / "child"
                granddir = Path(subdir) / "grandchild"
                os.makedirs(granddir)

                self.assertFalse(is_git_folder(subdir))
                self.assertFalse(is_git_folder(granddir))

                subprocess.run(
                    ["git", "init"],
                    cwd=subdir,
                    capture_output=True
                )

                self.assertTrue(is_git_folder(subdir))
                self.assertTrue(is_git_folder(granddir))

    def test_commit_exists(self):
        with tempfile.TemporaryDirectory() as git_repo:
            # All of this is setting up a simple git repo with a single commit.
            subprocess.run(
                ["git", "init"],
                cwd=git_repo,
                capture_output=True
            )

            subprocess.run(
                ["touch", "world.txt"],
                cwd=git_repo,
                capture_output=True
            )

            subprocess.run(
                ["git", "add", "world.txt"],
                cwd=git_repo,
                capture_output=True
            )

            subprocess.run(
                ["git", "commit", "-m", "Init"],
                cwd=git_repo,
                capture_output=True
            )

            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=git_repo,
                capture_output=True
            ).stdout

            self.assertTrue(commit_exists(Path(git_repo), head.decode()))


log_file_content = """
2026-01-07T23:02:45.275773Z Saw new cmpctblock header hash=000000000000000000012fc6f93961410622efe585fd5ebd6e203e2cdb85642d height=931340 peer=21
2026-01-07T23:02:45.275840Z [cmpctblock] Initializing PartiallyDownloadedBlock for block 000000000000000000012fc6f93961410622efe585fd5ebd6e203e2cdb85642d using a cmpctblock of 29312 bytes
2026-01-07T23:02:45.279488Z [cmpctblock] Initialized PartiallyDownloadedBlock for block 000000000000000000012fc6f93961410622efe585fd5ebd6e203e2cdb85642d using a cmpctblock of 29312 bytes
2026-01-07T23:02:45.280218Z [cmpctblock] Successfully reconstructed block 000000000000000000012fc6f93961410622efe585fd5ebd6e203e2cdb85642d with 1 txn prefilled (473 bytes), 4789 txn from mempool (1765894 bytes), 2 txn from extrapool (567 bytes)), and 0 txn requested (0 bytes)
2026-01-07T23:02:45.280223Z [cmpctblock] 0 txn (0 bytes) of the prefill were redundant, 0 txn (0 bytes) were present in the mempool, 0 txn (0 bytes) were present in the extrapool. 
2026-01-07T23:02:45.289193Z [bench]   - Using cached block
2026-01-07T23:02:45.289205Z [bench]   - Load block from disk: 0.01ms
2026-01-07T23:02:45.289217Z [bench]     - Sanity checks: 0.00ms [0.00s (0.00ms/blk)]
2026-01-07T23:02:45.289232Z [bench]     - Fork checks: 0.02ms [0.00s (0.02ms/blk)]
2026-01-07T23:02:45.295807Z [bench]       - Connect 4792 transactions: 6.57ms (0.001ms/tx, 0.001ms/txin) [0.13s (14.72ms/blk)]
2026-01-07T23:02:45.295813Z [bench]     - Verify 9444 txins: 6.58ms (0.001ms/txin) [0.13s (14.95ms/blk)]
2026-01-07T23:02:45.296699Z [bench]     - Write undo data: 0.89ms [0.01s (0.97ms/blk)]
2026-01-07T23:02:45.296703Z [bench]     - Index writing: 0.00ms [0.00s (0.01ms/blk)]
2026-01-07T23:02:45.296806Z [bench]   - Connect total: 7.61ms [0.15s (16.12ms/blk)]
2026-01-07T23:02:45.298224Z [bench]   - Flush: 1.42ms [0.02s (2.46ms/blk)]
2026-01-07T23:02:45.298228Z [bench]   - Writing chainstate: 0.01ms [0.00s (0.01ms/blk)]
2026-01-07T23:02:45.311063Z UpdateTip: new best=000000000000000000012fc6f93961410622efe585fd5ebd6e203e2cdb85642d height=931340 version=0x20086000 log2_work=96.028066 tx=1295024154 date='2026-01-07T23:02:41Z' progress=1.000000 cache=18.3MiB(138142txo)
2026-01-07T23:02:45.311078Z [bench]   - Connect postprocess: 12.85ms [2.73s (303.79ms/blk)]
2026-01-07T23:02:45.311081Z [bench] - Connect block: 21.89ms [2.90s (322.39ms/blk)]
"""


class TestGrepCommands(unittest.TestCase):
    def test_rg_filter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "debug.log"
            test_file.write_text(log_file_content)

            scenarios = [
                (["Nothing matches this!"], []),
                (["Flush"], ["2026-01-07T23:02:45.298224Z [bench]   - Flush: 1.42ms [0.02s (2.46ms/blk)]"]),
                (["Flush", "Using"],[
                    "2026-01-07T23:02:45.289193Z [bench]   - Using cached block",
                    "2026-01-07T23:02:45.298224Z [bench]   - Flush: 1.42ms [0.02s (2.46ms/blk)]"
                ])
            ]

            for filters, expected in scenarios:
                with self.subTest(filters=filters):
                    result = rg_filter(filters, test_file)
                    # Sort both to ensure comparison works regardless of order
                    self.assertEqual(result, expected)

    def test_rg_filter_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(RuntimeError, "Error filtering logfile!"):
                rg_filter(["test"], Path(tmpdir) / "nonexistent")
