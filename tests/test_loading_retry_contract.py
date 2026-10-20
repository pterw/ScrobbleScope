"""Retry on the loading page posts every field the search form posts.

A retry that drops a field re-runs a different search without telling the
listener (Retry once re-ran an "Include" search as "Hide").
`retryCurrentSearch()` rebuilds the POST to /results_loading from the
`scrobble-config` block in loading.html, both written by hand, so this test
derives the route's field set from its source and checks both copies.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# csrf_token is posted from the meta tag, not from the config block.
NOT_CONFIG = {"csrf_token"}


def _route_fields() -> set[str]:
    source = (ROOT / "scrobblescope" / "routes" / "album_flow.py").read_text(
        encoding="utf-8"
    )
    func = next(
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.FunctionDef) and n.name == "results_loading"
    )
    fields: set[str] = set()
    for node in ast.walk(func):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and ast.unparse(node.func.value) == "request.form"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            fields.add(node.args[0].value)
        elif (
            isinstance(node, ast.Subscript)
            and ast.unparse(node.value) == "request.form"
            and isinstance(node.slice, ast.Constant)
        ):
            fields.add(node.slice.value)
    return fields


def _config_keys() -> set[str]:
    html = (ROOT / "templates" / "loading.html").read_text(encoding="utf-8")
    block = re.search(
        r'id="scrobble-config"[^>]*>\{\{\s*(\{.*?\})\s*\|\s*tojson', html, re.S
    )
    assert block, "scrobble-config block not found in loading.html"
    return set(re.findall(r'"(\w+)"\s*:', block.group(1)))


def _posted_names() -> set[str]:
    js = (ROOT / "static" / "js" / "loading.js").read_text(encoding="utf-8")
    start = js.index("function retryCurrentSearch")
    return set(re.findall(r"createHiddenInput\('(\w+)'", js[start:]))


def test_route_fields_are_found():
    fields = _route_fields()
    assert {"username", "year", "sort_by", "include_unmatched"} <= fields


def test_every_route_field_is_in_the_loading_config():
    missing = _route_fields() - NOT_CONFIG - _config_keys()
    assert not missing, f"loading.html scrobble-config lacks {sorted(missing)}"


def test_retry_posts_every_route_field():
    missing = _route_fields() - _posted_names()
    assert not missing, f"retryCurrentSearch() does not post {sorted(missing)}"
