from pathlib import Path
import re
from typing import Callable
from leave.commands import rg_filter
from leave.metadata import LogEntry

type LogPatternCallback = Callable[[LogEntry, dict], None]


class LogPattern:
    regex: str
    # Exists strictly for performance reasons. (todo: may not be true anymore
    # since switching to ripgrep, check)
    regex_nocapture: str
    callback: LogPatternCallback

    def __init__(self, regex: str | re.Pattern, regex_nocapture: str | re.Pattern, callback: LogPatternCallback):
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


def leavelog(logfile: Path, logpatterns: list[LogPattern]):
    filter_patterns: list[str] = [p.regex_nocapture for p in logpatterns]
    filtered_lines = rg_filter(filter_patterns, logfile)

    compiled_patterns = [(re.compile(p.regex), p) for p in logpatterns]

    for line in filtered_lines:
        for regex, pattern in compiled_patterns:
            match = regex.search(line)
            if match:
                entry = LogEntry(line)
                pattern.callback(entry, match.groupdict())
                break
