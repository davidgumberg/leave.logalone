import subprocess
import os
import sys

def is_git_folder(path):
    is_work_tree = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
        capture_output=True
    )

    return is_work_tree.returncode == 0


print(is_git_folder("/tmp"))
