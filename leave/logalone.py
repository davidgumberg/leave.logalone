import re

from pathlib import Path

from leave.commands import rg_filter
from leave.logpattern import LogPattern
from leave.metadata import LogEntry


def isolate(logfile: Path, logpatterns: list[LogPattern]):
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
