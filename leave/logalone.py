import re

from datetime import datetime
from pathlib import Path
from typing import Optional

from leave.commands import rg_filter
from leave.logpattern import LogPattern
from leave.metadata import LogEntry


def isolate(logfile: Path, logpatterns: list[LogPattern],
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None) -> None:
    filter_patterns: list[str] = [p.regex_nocapture for p in logpatterns]
    filtered_lines = rg_filter(filter_patterns, logfile)

    compiled_patterns = [(re.compile(p.regex), p) for p in logpatterns]

    for line in filtered_lines:
        entry = LogEntry(line, eager=False)
        if start_date and entry.time() < start_date:
            continue
        if end_date and entry.time() >= end_date:
            # We assume (reasonably) that the lines are in order.
            break

        for regex, pattern in compiled_patterns:
            match = regex.search(entry.body_str)
            if match:
                entry.process_line_metadata()
                pattern.callback(entry, **match.groupdict())
                break
