"""Tests for the check-selection manifest (`frontend_gate_checks.toml`).

Selection is by check name only. `frontend_gate.CHECKS` stays the full,
structural registry every other test in this package relies on -- these
tests cover the separate selection layer that decides which of those
checks actually run.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from scripts.dev import frontend_gate
from scripts.dev.frontend_gate import FrontendGateError


def test_disabling_divider_contrast_drops_planned_runs_by_two() -> None:
    """`divider contrast` runs on one profile (DESKTOP) but sits in
    STATIC_ASSETS, the group Firefox also runs as its canary. Disabling it
    therefore drops two planned runs, not one: one profile, both engines.
    """
    before = frontend_gate._selected_runs(frozenset())
    after = frontend_gate._selected_runs(frozenset({"divider contrast"}))

    assert before - after == 2


def test_disabled_check_name_is_reported_in_the_header() -> None:
    """A disabled check's name must be visible, not silently dropped."""
    header = frontend_gate._selection_header(frozenset({"divider contrast"}))

    assert "divider contrast" in header


def test_disabling_a_required_check_is_refused(tmp_path) -> None:
    """A required check can never be disabled -- the manifest refuses it."""
    manifest = tmp_path / "frontend_gate_checks.toml"
    manifest.write_text(
        'required = ["stylesheet isolation"]\ndisabled = ["stylesheet isolation"]\n'
    )

    with pytest.raises(FrontendGateError, match="stylesheet isolation"):
        frontend_gate._load_check_manifest(manifest)


def test_unknown_check_name_is_refused_not_ignored(tmp_path) -> None:
    """A typo in the manifest must stop the gate, not silently keep the
    check enabled.
    """
    manifest = tmp_path / "frontend_gate_checks.toml"
    manifest.write_text('required = []\ndisabled = ["divider kontrast"]\n')

    with pytest.raises(FrontendGateError, match="divider kontrast"):
        frontend_gate._load_check_manifest(manifest)


def test_missing_manifest_is_refused_with_a_path(tmp_path) -> None:
    """A missing manifest fails fast, naming the path (Fail Fast)."""
    missing = tmp_path / "does_not_exist.toml"

    with pytest.raises(FrontendGateError, match="does_not_exist.toml"):
        frontend_gate._load_check_manifest(missing)


def test_malformed_manifest_is_refused_not_a_traceback(tmp_path) -> None:
    """Invalid TOML fails fast with the path, not a bare TOMLDecodeError."""
    manifest = tmp_path / "frontend_gate_checks.toml"
    manifest.write_text("required = [\n")

    with pytest.raises(FrontendGateError, match="frontend_gate_checks.toml"):
        frontend_gate._load_check_manifest(manifest)


def test_run_checks_skips_a_disabled_check(monkeypatch) -> None:
    """Disabling a check by name must actually stop it from running, not
    just lower the printed count.
    """
    seen = []

    def _skipped(_page, _base_url):
        seen.append("skipped")
        return []

    def _kept(_page, _base_url):
        seen.append("kept")
        return []

    monkeypatch.setattr(
        frontend_gate,
        "CHECKS",
        (
            ("skip me", _skipped, (frontend_gate.DESKTOP,), "g1"),
            ("keep me", _kept, (frontend_gate.DESKTOP,), "g1"),
        ),
    )
    monkeypatch.setattr(frontend_gate, "DISABLED_CHECKS", frozenset({"skip me"}))

    failures = frontend_gate.run_checks(
        new_page=lambda spec: Mock(), base_url="http://127.0.0.1:0"
    )

    assert seen == ["kept"]
    assert failures == []


def test_the_shipped_manifest_loads_and_keeps_required_checks_enabled() -> None:
    """The committed manifest must itself be valid: it is loaded at import,
    so a bad edit to it breaks every test in this package, not just this one.
    """
    required, disabled = frontend_gate._load_check_manifest()

    assert set(required) == {
        "stylesheet isolation",
        "theme tokens",
        "pipeline state machines",
        "unmatched report",
    }
    assert disabled == frozenset()
    assert frontend_gate.REQUIRED_CHECKS == required
    assert frontend_gate.DISABLED_CHECKS == disabled
