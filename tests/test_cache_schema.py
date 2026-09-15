import ast
from pathlib import Path

INIT_DB_SOURCE = Path("init_db.py").read_text(encoding="utf-8")


def _string_constants():
    """Every string literal in init_db.py, so a statement can be searched
    for regardless of which conn.execute() call it lives in."""
    tree = ast.parse(INIT_DB_SOURCE)
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def test_adds_provider_columns_to_spotify_cache():
    constants = _string_constants()
    assert any(
        "ALTER TABLE spotify_cache" in c
        and "ADD COLUMN IF NOT EXISTS provider TEXT" in c
        for c in constants
    )
    assert any(
        "ALTER TABLE spotify_cache" in c
        and "ADD COLUMN IF NOT EXISTS provider_album_id TEXT" in c
        for c in constants
    )
    assert any(
        "ALTER TABLE spotify_cache" in c
        and "ADD COLUMN IF NOT EXISTS provider_url TEXT" in c
        for c in constants
    )


def test_drops_not_null_on_spotify_id():
    constants = _string_constants()
    assert any(
        "ALTER TABLE spotify_cache" in c
        and "ALTER COLUMN spotify_id DROP NOT NULL" in c
        for c in constants
    )


def test_backfills_provider_for_existing_rows():
    constants = _string_constants()
    assert any(
        "UPDATE spotify_cache" in c and "SET provider" in c and "provider_album_id" in c
        for c in constants
    )


def test_creates_original_release_cache_table():
    constants = _string_constants()
    matches = [
        c for c in constants if "CREATE TABLE IF NOT EXISTS original_release_cache" in c
    ]
    assert matches, "original_release_cache table statement not found"
    stmt = matches[0]
    for column in (
        "artist_norm",
        "album_norm",
        "mb_release_group",
        "original_release",
        "checked_at",
        "PRIMARY KEY (artist_norm, album_norm)",
    ):
        assert column in stmt
