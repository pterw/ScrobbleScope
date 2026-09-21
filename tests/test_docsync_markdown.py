"""Shared Markdown scanner regressions."""

import pytest
from docsync.markdown import fully_struck, marker_lines, prose_lines


@pytest.mark.parametrize("fence", ["```", "~~~", "````", "~~~~"])
def test_fenced_headings_are_not_prose(fence):
    assert prose_lines([fence + "markdown", "## Fake", fence, "## Real"]) == [
        (3, "## Real")
    ]


def test_short_or_different_fence_does_not_close():
    assert prose_lines(["````", "```", "~~~", "## Fake", "`````", "## Real"]) == [
        (5, "## Real")
    ]


def test_comments_preserve_original_line_indices():
    assert prose_lines(["<!--", "## Fake", "-->", "## Real", "<!-- ## Fake -->"]) == [
        (3, "## Real")
    ]


def test_inline_comment_preserves_surviving_prose_offsets():
    line = "prefix <!-- hidden --> ~~old~~ suffix"
    scanned = prose_lines([line])
    assert scanned == [
        (0, "prefix " + " " * len("<!-- hidden -->") + " ~~old~~ suffix")
    ]
    assert scanned[0][1].index("old") == line.index("old")
    assert fully_struck(scanned[0][1], line.index("old"), line.index("old") + 3)


def test_partial_strike_is_not_full_exemption():
    assert not fully_struck("~~old~~ still prescribed", 2, 23)
    assert fully_struck("~~old still prescribed~~", 2, 22)


def test_standalone_docsync_marker_is_not_prose():
    assert prose_lines(["<!-- DOCSYNC:STATUS-START -->", "real"]) == [(1, "real")]


def test_marker_examples_are_not_real_markers():
    marker = "<!-- DOCSYNC:STATUS-START -->"
    assert [
        (index, line)
        for index, line in marker_lines(["~~~", marker, "~~~", "<!--", marker, marker])
        if line == marker
    ] == [(5, marker)]
