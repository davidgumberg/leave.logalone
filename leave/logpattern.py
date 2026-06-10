import re
from typing import Callable

LogPatternCallback = Callable[..., None]


class LogPattern:
    regex: str
    # Exists for performance reasons and for being able to specify a subset of
    # the log message, e.g. for `net: receive cmpctblock`.
    regex_filter: str
    callback: LogPatternCallback

    def __init__(self, regex: str | re.Pattern, regex_filter: str | re.Pattern,
                 callback: LogPatternCallback):
        match regex:
            case str():
                self.regex = regex
            case re.Pattern():
                self.regex = regex.pattern

        match regex_filter:
            case str():
                self.regex_nocapture = regex_filter
            case re.Pattern():

                self.regex_nocapture = regex_filter.pattern

        self.callback = callback
