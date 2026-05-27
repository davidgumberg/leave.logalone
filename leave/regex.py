import re

def regex_add_names(pattern: str, names: list[str]) -> re.Pattern:
    """
    Takes a regex and adds a list of names for all of the '(.*)' matches
    in the pattern.
    """

    anymatches = re.findall(r'\(\.\*\)', pattern)
    if len(anymatches) != len(names):
        raise ValueError(f"regex_add_names passed a list of incorrect "
                         f"length {len(names)}. Expected {len(anymatches)} "
                         f"for pattern {pattern}!")

    if len(names) != len(set(names)):
        raise ValueError("regex_add_names must be given unique names!")

    for name in names:
        pattern = pattern.replace(r'(.*)', f'(?P<{name}>.*)', 1)

    return re.compile(pattern)


def fmt_to_regex(fmt_str: str, grouped: bool = True) -> re.Pattern:
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

    if grouped:
        pattern = re.sub(specifier_pattern, r'(.*)', pattern)
    else:
        pattern = re.sub(specifier_pattern, r'.*', pattern)
    pattern = pattern.replace(percent_placeholder, "%")

    return re.compile(pattern)
