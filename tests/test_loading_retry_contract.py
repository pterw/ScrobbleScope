"""Retry on the loading page posts every field the search form posts.

A retry that drops a field re-runs a different search without telling the
listener (Retry once re-ran an "Include" search as "Hide").
`retryCurrentSearch()` rebuilds the POST to /results_loading from the
`scrobble-config` block in loading.html, both written by hand, so this test
reads the field set from `album_request.FORM_FIELDS` and checks both copies.
"""

from __future__ import annotations

import re
from pathlib import Path

from scrobblescope.album_request import FORM_FIELDS

ROOT = Path(__file__).resolve().parent.parent
# csrf_token is posted from the meta tag, not from the config block.
NOT_CONFIG = {"csrf_token"}


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
    assert "include_unmatched" in FORM_FIELDS and len(FORM_FIELDS) == 10


def test_every_route_field_is_in_the_loading_config():
    missing = set(FORM_FIELDS) - NOT_CONFIG - _config_keys()
    assert not missing, f"loading.html scrobble-config lacks {sorted(missing)}"


def test_retry_posts_every_route_field():
    missing = set(FORM_FIELDS) - _posted_names()
    assert not missing, f"retryCurrentSearch() does not post {sorted(missing)}"
