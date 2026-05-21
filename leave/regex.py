from ctypes import ArgumentError
import re


def regex_add_names(r: re.Pattern, names: list[str]) -> re.Pattern:
    """
    Takes a regex and adds a list of names for all of the '(.*)' matches
    in the pattern.
    """

    pattern: str = r.pattern

    anymatches = re.findall(pattern, r'(.*)')
    if len(anymatches) != len(names):
        raise ArgumentError(f"regex_add_names was given {len(names)} names, "
                            "to use for {len(anymatches)} matches of '(.*)' "
                            "in pattern: {r.pattern}")

    for name in names:
        pattern = pattern.replace(r'(.*)', f'(?P<{name}>.*', 1)

    return re.compile(pattern)


def fmt_to_regex(fmt_str: str) -> re.Pattern:
    """
    Converts a printf/scanf string to a Python Regex.
    Returns the regex string and a list of inferred types, just a wrapper
    for the python scanf package's scanf_compile.
    """

    # Strip the sometimes-trailing newline, FIXME but for now I think this
    # is the only escape sequence used?
    pattern = fmt_str.replace("\n", "")
    pattern = re.escape(pattern)

    # temp to avoid matching %%
    percent_placeholder = "___PERCENT_LITERAL___"
    pattern = pattern.replace("%%", percent_placeholder)

    # the pattern is pure slop, looks right if i squint right
    specifier_pattern = r'%[-+0 #]*[\d\*]*(\.[\d\*]*)?[hljztL]*[diuoxXfFeEgGaAcspn]'

    pattern = re.sub(specifier_pattern, r'(.*)', pattern)
    pattern = pattern.replace(percent_placeholder, "%")

    return re.compile(pattern)
