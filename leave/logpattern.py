import re
from typing import Callable

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
