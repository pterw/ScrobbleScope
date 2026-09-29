"""Behavior tests for the untracked-essentials WARNING check (F-B21-25)."""

from pathlib import Path

from scripts.dev._worktree_guard_essentials import essentials_diagnostics

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_the_real_config_declares_no_untracked_essentials():
    """`config/docsync.toml` no longer declares `skills-lock.json` (owner
    ruling 2026-09-28: nothing in this repository reads it), so a real
    checkout must be silent even though the file itself is gitignored and
    typically absent.
    """
    assert essentials_diagnostics(REPO_ROOT) == []


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


def test_a_malformed_table_warns_instead_of_raising(tmp_path: Path):
    """CR1: a bad [untracked_essentials] table must stay WARNING-only.

    Before the fix, DeclarationError escaped to `inspect_worktree`'s
    fail-closed `except Exception` and replaced the whole guard result with
    ERROR WT014.
    """
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "docsync.toml").write_text(
        '[untracked_essentials]\npaths = "skills-lock.json"\n', encoding="utf-8"
    )
    diagnostics = essentials_diagnostics(tmp_path)
    assert [(d.code, d.severity) for d in diagnostics] == [("WT015", "WARNING")]
    assert diagnostics[0].subject == "config/docsync.toml"
    assert "paths" in diagnostics[0].message


def test_a_non_utf8_declarations_file_warns_instead_of_raising(tmp_path: Path):
    """Finding 5: a read error must stay WARNING, not escape as WT014.

    Before the fix, `load_declarations` caught only `tomllib.TOMLDecodeError`
    around `read_text`, so `UnicodeDecodeError` escaped `essentials_diagnostics`
    (which catches only `DeclarationError`) and reached `inspect_worktree`'s
    fail-closed ERROR WT014.
    """
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "docsync.toml").write_bytes(
        b"[untracked_essentials]\n# \xff\xfe not utf-8\n"
    )
    diagnostics = essentials_diagnostics(tmp_path)
    assert [(d.code, d.severity) for d in diagnostics] == [("WT015", "WARNING")]
    assert diagnostics[0].subject == "config/docsync.toml"
    assert "the declarations file could not be read" in diagnostics[0].message


def test_an_unreadable_declarations_path_warns_instead_of_raising(
    tmp_path: Path, monkeypatch
) -> None:
    """The same OSError conversion, exercised through the guard's own entry point."""
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "docsync.toml").write_text(
        '[untracked_essentials]\npaths = ["skills-lock.json"]\n', encoding="utf-8"
    )

    def _raise_os_error(self, *args, **kwargs):
        raise OSError("simulated: file is locked")

    monkeypatch.setattr(Path, "read_text", _raise_os_error)

    diagnostics = essentials_diagnostics(tmp_path)
    assert [(d.code, d.severity) for d in diagnostics] == [("WT015", "WARNING")]
    assert diagnostics[0].subject == "config/docsync.toml"
    assert "the declarations file could not be read" in diagnostics[0].message


def test_the_wt015_message_names_the_file_not_only_the_table(tmp_path: Path):
    """WT015's message must not blame [untracked_essentials] when the TOML
    error is a parse failure that has nothing to do with that table
    (finding 5's second half): the parse fails before any table is read.
    """
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "docsync.toml").write_text("[[value\n", encoding="utf-8")
    diagnostics = essentials_diagnostics(tmp_path)
    assert [(d.code, d.severity) for d in diagnostics] == [("WT015", "WARNING")]
    assert "the declarations file could not be read" in diagnostics[0].message
    assert (
        "[untracked_essentials] declaration could not be read"
        not in diagnostics[0].message
    )
    assert "not valid TOML" in diagnostics[0].message


def test_a_declared_path_that_is_a_directory_warns_distinctly(tmp_path: Path):
    """CR10: a declared path that is a directory must not read as "missing".

    Before the fix, `essentials_diagnostics` checked only `Path.is_file()`, so
    a declared directory failed the same test as a genuinely absent path and
    was reported "missing" -- sending the reader to restore something that
    was there all along.
    """
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "docsync.toml").write_text(
        '[untracked_essentials]\npaths = ["a_directory"]\n', encoding="utf-8"
    )
    (tmp_path / "a_directory").mkdir()
    diagnostics = essentials_diagnostics(tmp_path)
    assert [(d.code, d.severity) for d in diagnostics] == [("WT015", "WARNING")]
    assert diagnostics[0].subject == "a_directory"
    assert "is a directory, not a file" in diagnostics[0].message
    assert "missing" not in diagnostics[0].message
