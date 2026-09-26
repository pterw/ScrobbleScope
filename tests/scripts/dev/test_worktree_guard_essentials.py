"""Behavior tests for the untracked-essentials WARNING check (F-B21-25)."""

from pathlib import Path

from scripts.dev._worktree_guard_essentials import essentials_diagnostics


def test_a_missing_declared_path_warns(tmp_path: Path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "docsync.toml").write_text(
        '[untracked_essentials]\npaths = ["skills-lock.json"]\n', encoding="utf-8"
    )
    diagnostics = essentials_diagnostics(tmp_path)
    assert [(d.code, d.severity) for d in diagnostics] == [("WT015", "WARNING")]
    assert diagnostics[0].subject == "skills-lock.json"


def test_a_present_declared_path_is_silent(tmp_path: Path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "docsync.toml").write_text(
        '[untracked_essentials]\npaths = ["skills-lock.json"]\n', encoding="utf-8"
    )
    (tmp_path / "skills-lock.json").write_text("{}", encoding="utf-8")
    assert essentials_diagnostics(tmp_path) == []


def test_no_declaration_is_silent(tmp_path: Path):
    assert essentials_diagnostics(tmp_path) == []
