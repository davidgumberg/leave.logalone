import re
import sys

from collections.abc import Callable

from leave.metadata import LogEntry

from leave.db import (
    LogDB,
)


if __name__ == "__main__":
    if len(sys.argv) not in [2, 3, 4]:
        print(
            "Usage!!! logextractor.py {src_dir} {out_path}\n"
            "Or!!! logextractor.py {src_dir} {file} {out_path}\n"
            )
        sys.exit(-1)

    compiler = LogDB()
    if len(sys.argv) == 3:
        compiler.parse(sys.argv[1])
    elif len(sys.argv) == 4:
        compiler.parse(sys.argv[1], sys.argv[2])
    compiler.dump_to_file(sys.argv[-1])
