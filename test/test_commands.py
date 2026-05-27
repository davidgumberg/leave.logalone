import os
import subprocess
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch


from leave.commands import (
    commit_exists,
    is_git_folder
)


class TestCommands(unittest.TestCase):
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
