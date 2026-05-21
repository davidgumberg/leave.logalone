import os
import subprocess
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch


from leave.commands import (
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
                subdir = f"{topdir}/child"
                granddir = f"{subdir}/grandchild"
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
