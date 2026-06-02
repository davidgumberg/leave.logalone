# Takes multiple literals and turns them into a single literal, cannot handle
# preprocessor macros in between literals, throws a ValueError if not a simple
# case.
# e.g. printf("broken up" " " "string literal") -> if passed what's inside the parens,
# this function returns "broken up string literal"
def string_from_literals(string: str) -> str:
    out = []
    escaped = False
    in_literal = False
    for c in string:
        if escaped:
            escaped = False
            out.append(c)
            continue

        if c == '\\':
            escaped = True
            out.append(c)
            continue

        if c == "\"" and not escaped:
            in_literal = not in_literal
            continue

        if not in_literal:
            if not c.isspace():
                raise ValueError(f"non whitespace characters found outside of string literals! in {string}")
            continue

        out.append(c)
    if in_literal:
        raise ValueError(f"Unclosed string literal in {string}")
    return "".join(out)
