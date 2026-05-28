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

    return exists_ret.returncode == 0


def git_fetch(path: Path, hash: str) -> bool:
    fetch_ret = subprocess.run(
        ["git", "fetch", hash.strip()],
        cwd=path,
        capture_output=True
    )

    return fetch_ret.returncode == 0 and commit_exists(path, hash)


def get_commit_tmpdir(repo: Path, hash: str) -> TemporaryDirectory:
    if not is_git_folder(repo):
        raise Exception(f"{repo} is not a git folder.")

    if not commit_exists(repo, hash) and not git_fetch(repo, hash):
        raise Exception(f"{hash} not found in Upstream!")

    tmp_worktree = TemporaryDirectory()
    subprocess.run(
        ["git", "worktree", "add", tmp_worktree.name, hash],
        cwd=repo,
        capture_output=True
    )

    return tmp_worktree


def gen_compile_commands(path: Path) -> bool:
    ret = subprocess.run(
        [
            "cmake", 
            "-B", "build", 
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            "-DCMAKE_C_COMPILER=clang",
            "-DCMAKE_CXX_COMPILER=clang++"
        ],
        cwd=path,
        capture_output=True
    )
    return ret.returncode == 0
