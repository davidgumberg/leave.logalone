import subprocess
import os
import sys

from pathlib import Path
from tempfile import TemporaryDirectory


def is_git_folder(path: Path):
    is_work_tree = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
        capture_output=True
    )

    return is_work_tree.returncode == 0


def commit_exists(path: Path, hash: str) -> bool:
    exists_ret = subprocess.run(
       ["git", "cat-file", "-e", f"{hash.strip()}^{{commit}}"],
       cwd=path,
       capture_output=True
    )

    print(path.name)
    print(hash)

    return exists_ret.returncode == 0
