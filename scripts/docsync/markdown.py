"""Small shared scanner for normative Markdown, retaining source locations."""

import re
from collections.abc import Sequence

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_STRIKE = re.compile(r"~~.+?~~")


def prose_lines(lines: Sequence[str]) -> list[tuple[int, str]]:
    """Exclude fenced examples and comments without changing original indices."""
    return _scan(lines, preserve_markers=False)


def marker_lines(lines: Sequence[str]) -> list[tuple[int, str]]:
    """Expose real standalone DOCSYNC markers, never markers in examples."""
    return _scan(lines, preserve_markers=True)


def _scan(lines: Sequence[str], *, preserve_markers: bool) -> list[tuple[int, str]]:
    result = []
    fence_char = ""
    fence_length = 0
    in_comment = False
    for index, raw in enumerate(lines):
        if fence_char:
            closer = re.fullmatch(
                r" {0,3}" + re.escape(fence_char) + "{" + str(fence_length) + r",}\s*",
                raw,
            )
            if closer:
                fence_char = ""
            continue
        if (
            preserve_markers
            and not in_comment
            and re.fullmatch(r"\s*<!-- DOCSYNC:[A-Z-]+ -->\s*", raw)
        ):
            result.append((index, raw))
            continue
        # Replace comments with spaces so offsets in surviving prose remain valid.
        visible = ""
        position = 0
        while position < len(raw):
            if in_comment:
                end = raw.find("-->", position)
                if end < 0:
                    visible += " " * (len(raw) - position)
                    break
                visible += " " * (end + 3 - position)
                position = end + 3
                in_comment = False
            else:
                start = raw.find("<!--", position)
                if start < 0:
                    visible += raw[position:]
                    break
                visible += raw[position:start]
                position = start
                in_comment = True
        opener = _FENCE.match(visible)
        if opener and not (opener.group(1)[0] == "`" and "`" in opener.group(2)):
            fence_char = opener.group(1)[0]
            fence_length = len(opener.group(1))
            continue
        if visible.strip() or not raw.strip():
            result.append((index, visible))
    return result


def fully_struck(line: str, start: int, end: int) -> bool:
    """Whether the complete match lies inside one strikethrough span."""
    return any(
        span.start() + 2 <= start and end <= span.end() - 2
        for span in _STRIKE.finditer(line)
    )
