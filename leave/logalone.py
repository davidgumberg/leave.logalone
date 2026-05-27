import re
import sys

from collections.abc import Callable
from typing import Optional

from .db import (
    LogDB,
    LogMessage
)


class LogPattern:
    regex: str
    # Exists strictly for performance reasons.
    regex_nocapture: str
    callback: Callable[[], None]

    def __init__(self, regex: str | re.Pattern, regex_nocapture: str | re.Pattern, callback: Callable[[], None]):
        match regex:
            case str():
                self.regex = regex
            case re.Pattern():
                self.regex = regex.pattern

        match regex_nocapture:
            case str():
                self.regex_nocapture = regex_nocapture
            case re.Pattern():
                self.regex_nocapture = regex_nocapture.pattern

        self.callback = callback


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
