"""CLI entry point, file I/O, and path constants for docsync.

Five modes share one corpus reader. `--check` reports, `--fix` repairs what a
renderer owns, `--split-archive` performs the historical one-time migration,
`--close-batch` performs the multi-document batch transition, and
`--paginate-archives` / `--cold-storage` are the explicit archive maintenance
runs.

Two orderings in this module are load-bearing.

History is read *flattened* -- through `ArchiveStore`, across hot and cold
pages alike -- before `_sync` runs and before any integrity check evaluates
test-count authority. An archive that has become an index reads identically to
the monolith it replaced, so paginating history or moving an old page to cold
storage can never change which recorded test result is the current one.

And nothing is written until the whole candidate corpus has been computed and
validated. Every writing mode -- including `--split-archive` -- publishes
through `docsync.transaction`, which takes the single-writer lock, proves
every source it read is unchanged, journals each before-image, and restores
all of them if any part of the write fails. A half-performed close-out, or a
half-performed archive split, is worse than none.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from docsync import findings as findings_module
from docsync.archives import (
    INDEX_START_MARKER,
    ArchiveStore,
    normalize,
    structure_issue,
)
from docsync.closeout import (
    ARCHIVED_DEFINITIONS_DIR,
    collect_transition_issues,
    find_batch_index_row,
    read_closeout_record,
    render_archived_definition,
    render_batch_index_row,
)
from docsync.declarations import (
    DECLARATIONS_FILENAME,
    DocumentsConfig,
    load_archive_config,
    load_closeout_config,
    load_documents_config,
    load_test_count_config,
)
from docsync.integrity import (
    _FINDINGS_HEADER_END_RE,
    FINDINGS_HEADER_COUNT_RE,
    LIVE_DOCUMENT_RELATIVE_PATHS,
    SESSION_CONTEXT_RELATIVE_PATH,
    _active_definition_reference,
    _definition_wp_numbers,
    collect_integrity_issues,
    collect_tracked_paths,
    resolved_live_document_paths,
)
from docsync.logic import (
    _merge_entries_into_log,
    _split_archive,
    _sync,
)
from docsync.models import IntegrityIssue, SyncError
from docsync.parser import (
    CURRENT_BATCH_END_MARKER,
    CURRENT_BATCH_START_MARKER,
    SECTION_4_RE,
    _find_marker_pair,
    _find_section,
    _parse_entries,
    root_definition_pattern,
)
from docsync.renderer import (
    _remove_marker_lines,
    _trim_trailing_blank,
    rewrite_recorded_counts,
)
from docsync.transaction import publish

REPO_ROOT = Path(".")
# Set from --config for the length of one main() invocation, and restored to
# None in its finally. REPO_ROOT is a true constant with no existing pattern
# to copy for a value that changes per run.
CONFIG_PATH: Path | None = None
ARCHIVE_PATH = Path("docs/logarchive/PLAYBOOK_EXECUTION_LOG_ARCHIVE.md")
# Derived from integrity.py's canonical relative-path strings, not restated:
# see the comment on LIVE_DOCUMENT_RELATIVE_PATHS there for why that module
# holds the one definition and this one builds Path objects from it.
SESSION_CONTEXT_PATH = Path(SESSION_CONTEXT_RELATIVE_PATH)
LOGS_DIR = Path("docs/history/logs")
DEFINITIONS_DIR = Path("docs/history/definitions")
FINDINGS_ARCHIVE_PATH = Path(findings_module.ARCHIVE_PATH)
LIVE_DOCUMENT_PATHS = tuple(Path(relative) for relative in LIVE_DOCUMENT_RELATIVE_PATHS)

_BATCH_LOG_RE = re.compile(r"^BATCH(\d+)_LOG\.md$", re.IGNORECASE)
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _batch_filename_candidates(directory: Path, name_re: re.Pattern[str]) -> list[Path]:
    """Scan a directory listing for BATCH* files, matched the same way everywhere.

    `Path.glob`'s case sensitivity follows the OS (insensitive on Windows,
    sensitive on POSIX) while every regex this module already filters glob's
    candidates with (`_BATCH_LOG_RE`, `root_definition_pattern`) is
    `re.IGNORECASE` -- that mismatch meant a lower-case batch file was visible
    to discovery on Windows and invisible on Linux (F-DOCSYNC-6); scanning the
    listing directly with the same regex everywhere makes discovery identical
    on every platform.
    """
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.iterdir() if name_re.match(path.name))


def _get_batch_log_path(batch_num: int) -> Path:
    """Return the canonical path for a per-batch execution log file."""
    return LOGS_DIR / f"BATCH{batch_num}_LOG.md"


def _check_root_batch_files(root: Path) -> list[str]:
    """Scan root for unarchived BATCH*.md files and return warning strings."""
    warnings = []
    for f in _batch_filename_candidates(
        root, re.compile(r"^BATCH.*\.md$", re.IGNORECASE)
    ):
        warnings.append(
            f"Root BATCH file detected: {f.name} should be archived under docs/history/definitions/."
        )
    return warnings


def _documents() -> DocumentsConfig:
    """Return the document paths declared for this invocation's config file."""
    return load_documents_config(REPO_ROOT, config_path=CONFIG_PATH)


def _declarations_path() -> Path:
    """Return the declarations file this invocation's config resolves to.

    Mirrors `docsync.declarations.load_declarations`'s own default so a
    corpus that reads document paths through it can name the file among the
    sources a publication must prove unchanged (`_Corpus.read_paths`).
    """
    return CONFIG_PATH if CONFIG_PATH is not None else REPO_ROOT / DECLARATIONS_FILENAME


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        raise SyncError(f"Required file is missing: {path}")
    return path.read_text(encoding="utf-8").splitlines()


def _read_lines_optional(path: Path) -> list[str] | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").splitlines()


def _render(lines: Sequence[str]) -> bytes:
    """Render managed lines the one way this tool writes a document.

    Every write path goes through this, so a document published inside a
    transaction is byte-identical to the same document written directly. A
    second rendering rule would make `--fix` and `--close-batch` disagree
    about trailing whitespace and report each other's output as drift.
    """
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _repository_relative(path: Path) -> str:
    """Return a normalized repository-relative key for integrity diagnostics."""
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def _repo_root() -> Path:
    """Return the absolute repository root every contained path resolves under."""
    return REPO_ROOT.resolve()


def _archive_store() -> ArchiveStore:
    """Build the archive reader/planner from this repository's own thresholds."""
    config = load_archive_config(REPO_ROOT, config_path=CONFIG_PATH)
    return ArchiveStore(_repo_root(), max_lines=config.max_lines)


def _is_index(path: Path) -> bool:
    """Whether this entry point has already become an index over pages."""
    if not path.is_file():
        return False
    return INDEX_START_MARKER in path.read_text(encoding="utf-8")


def _archive_text(store: ArchiveStore, path: Path) -> tuple[str, IntegrityIssue | None]:
    """Return one archive's flattened logical text, or its DOC020 diagnostic.

    A missing entry point is an empty archive rather than an error: the
    findings archive and the per-batch logs are created by the first rotation
    that needs them.
    """
    if not path.is_file():
        return "", None
    try:
        return store.read(path), None
    except SyncError as error:
        return "", structure_issue(_repository_relative(path), error)


def _archive_lines(
    store: ArchiveStore, path: Path
) -> tuple[list[str] | None, IntegrityIssue | None]:
    """Return an archive's logical lines, validating its physical layout.

    A legacy monolith returns its own bytes rather than the flattened
    rendering. The two agree on content, but not always on blank lines, and
    every drift comparison in this module is an equality test against the
    renderer's output: normalizing on read would report a document the
    renderer is happy with as drift, and `--fix` would rewrite it forever.
    """
    text, issue = _archive_text(store, path)
    if issue is not None:
        return None, issue
    if not path.is_file():
        return None, None
    if _is_index(path):
        return text.splitlines(), None
    return _read_lines(path), None


def _read_batch_log_lines(
    store: ArchiveStore,
) -> tuple[dict[int, list[str]], list[IntegrityIssue]]:
    """Read every per-batch log, flattened, with any layout diagnostics."""
    result: dict[int, list[str]] = {}
    issues: list[IntegrityIssue] = []
    if not LOGS_DIR.exists():
        return result, issues
    for batch_log_path in _batch_filename_candidates(LOGS_DIR, _BATCH_LOG_RE):
        match = _BATCH_LOG_RE.match(batch_log_path.name)
        if match is None:
            continue
        lines, issue = _archive_lines(store, batch_log_path)
        if issue is not None:
            issues.append(issue)
        elif lines is not None:
            result[int(match.group(1))] = lines
    return result, issues


def _archived_definitions() -> dict[str, list[str]]:
    """Read every archived batch definition the close-out gate may ask about.

    DOC019 is evaluated from `live_documents`, like every other document the
    integrity pass reads. Leaving the archived definitions out would make a
    correctly closed batch look like one whose definition had vanished, so
    the gate would report a defect that only its own blindness created.
    """
    directory = REPO_ROOT / ARCHIVED_DEFINITIONS_DIR
    if not directory.is_dir():
        return {}
    return {
        _repository_relative(path): _read_lines(path)
        for path in _batch_filename_candidates(
            directory, re.compile(r"^BATCH\d+_DEFINITION\.md$", re.IGNORECASE)
        )
    }


def _read_live_documents() -> dict[str, list[str]]:
    """Load canonical documents, root definitions and archived definitions."""
    live_documents = {
        _repository_relative(REPO_ROOT / relative): _read_lines(REPO_ROOT / relative)
        for relative in resolved_live_document_paths(_documents())
    }
    for definition_path in _batch_filename_candidates(
        REPO_ROOT, re.compile(r"^BATCH.*\.md$", re.IGNORECASE)
    ):
        live_documents[_repository_relative(definition_path)] = _read_lines(
            definition_path
        )
    live_documents.update(_archived_definitions())
    return live_documents


def _read_active_planned_wp_numbers(
    playbook_lines: list[str],
) -> tuple[int, ...] | None:
    """Read the valid active definition's finite work-package plan.

    Invalid, missing, and between-batch declarations return ``None`` so the
    renderer can retain its safe legacy fallback while DOC002 reports the
    declaration defect during the integrity pass.
    """
    current_batch, definition_path, _line, issue = _active_definition_reference(
        playbook_lines
    )
    if current_batch is None or definition_path is None or issue is not None:
        return None
    definition_lines = _read_lines_optional(REPO_ROOT / definition_path)
    if definition_lines is None:
        return None
    return _definition_wp_numbers(definition_lines)


def _format_issue(issue: IntegrityIssue) -> str:
    """Render one stable, repository-relative integrity diagnostic."""
    location = issue.path
    if issue.line is not None:
        location = f"{location}:{issue.line}"
    return (
        f"{issue.severity.upper()} {issue.code} {location} -- "
        f"{issue.invariant}\nRemediation: {issue.remediation}"
    )


class _Corpus:
    """Every document one invocation reasons about, read exactly once.

    The archives arrive flattened, so whatever reads this object sees one
    logical history regardless of how many files it is stored in. ``issues``
    carries the DOC020 diagnostics raised while reading: when it is not empty
    the remaining fields describe an archive whose layout disagrees with
    itself, and no mode may act on them.
    """

    def __init__(self, store: ArchiveStore) -> None:
        self.store = store
        self.issues: list[IntegrityIssue] = []
        self.declarations_path = _declarations_path()
        documents = _documents()
        playbook_path = REPO_ROOT / documents.playbook
        findings_path = REPO_ROOT / documents.findings
        self.findings_relative_path = documents.findings
        self.playbook_lines = _read_lines(playbook_path)
        if not ARCHIVE_PATH.exists():
            raise SyncError(f"Required file is missing: {ARCHIVE_PATH}")
        archive_lines, archive_issue = _archive_lines(store, ARCHIVE_PATH)
        if archive_issue is not None:
            self.issues.append(archive_issue)
        self.archive_lines = archive_lines if archive_lines is not None else []
        self.session_lines = _read_lines_optional(SESSION_CONTEXT_PATH)
        self.batch_log_lines, batch_issues = _read_batch_log_lines(store)
        self.issues.extend(batch_issues)
        self.findings_text = (
            findings_path.read_text(encoding="utf-8") if findings_path.is_file() else ""
        )
        self.findings_archive_text, findings_issue = _archive_text(
            store, FINDINGS_ARCHIVE_PATH
        )
        if findings_issue is not None:
            self.issues.append(findings_issue)
        self.live_documents = _read_live_documents()
        self.tracked_paths = collect_tracked_paths(REPO_ROOT)

    def rotation(self) -> findings_module.FindingRotation:
        """Plan the finding rotation this corpus permits, if any."""
        return findings_module.plan_findings(
            self.findings_text,
            self.findings_archive_text,
            active_path=self.findings_relative_path,
        )

    def read_paths(self) -> list[Path]:
        """Return every real path this corpus read, for a publication's proof.

        `transaction.publish` refuses to run unless it is handed every path
        the plan read, not only the ones it writes -- a document someone
        edited after the plan was computed but before publication must sink
        the run. Two call sites once hand-built that list themselves, and one
        of them silently fell behind `__init__` as documents were added here.
        Deriving the list from the corpus object instead means a document
        `__init__` starts reading tomorrow is covered by this method without
        anyone having to remember to update it.
        """
        paths = [REPO_ROOT / relative for relative in self.live_documents]
        paths.append(SESSION_CONTEXT_PATH)
        paths.append(self.declarations_path)
        paths.extend(_archive_members(ARCHIVE_PATH))
        paths.extend(_archive_members(FINDINGS_ARCHIVE_PATH))
        for batch_num in self.batch_log_lines:
            paths.extend(_archive_members(_get_batch_log_path(batch_num)))
        return paths


# ---------------------------------------------------------------------- #
# Publication                                                             #
# ---------------------------------------------------------------------- #


def _preimages(paths: Sequence[Path]) -> dict[Path, bytes | None]:
    """Record the exact bytes each path holds right now."""
    return {
        path: path.read_bytes() if path.is_file() else None
        for path in dict.fromkeys(paths)
    }


def _archive_members(path: Path) -> list[Path]:
    """Return an archive's entry point and every managed file beside it."""
    members = [path]
    for directory in ("pages", "cold"):
        folder = path.parent / directory
        if folder.is_dir() and not folder.is_symlink():
            members.extend(sorted(item for item in folder.iterdir() if item.is_file()))
    return members


def _verify_archive_candidate(
    store: ArchiveStore,
    path: Path,
    updates: Mapping[Path, bytes | None],
    expected_text: str,
) -> None:
    """Prove the planned corpus still reads back as the history it came from.

    The candidate is applied to a throwaway copy of the archive's directory
    and read back through a second store. Comparing the flattened result with
    the text that was planned checks entry identity, entry count and content
    fingerprint in one step -- and it does so *before* anything on disk moves,
    which is the only point at which refusing still costs nothing.
    """
    root = _repo_root()
    directory = path.resolve().parent
    relative_directory = directory.relative_to(root)
    with tempfile.TemporaryDirectory() as handle:
        mirror = Path(handle).resolve()
        shutil.copytree(directory, mirror / relative_directory)
        for target, payload in updates.items():
            destination = mirror / target.resolve().relative_to(root)
            if payload is None:
                destination.unlink(missing_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
        mirrored = ArchiveStore(mirror, max_lines=store.max_lines)
        rebuilt = mirrored.read(mirror / path.resolve().relative_to(root))
    if normalize(rebuilt) != normalize(expected_text):
        raise SyncError(
            f"The planned layout for {_repository_relative(path)} does not read "
            f"back as the history it was built from. Nothing was written."
        )


def _plan_archive(
    store: ArchiveStore,
    path: Path,
    lines: Sequence[str],
    *,
    as_of: dt.date | None = None,
    cold_days: int,
    paginate: bool,
) -> dict[Path, bytes | None]:
    """Return the writes that store ``lines`` in this archive's own layout.

    ``paginate`` is what separates ordinary repair from migration. An archive
    that is already an index is always planned through the store, because its
    entry point is a manifest and writing logical text over it would orphan
    every page. A legacy monolith is written as one file unless migration was
    explicitly asked for, so no ordinary `--fix` ever repaginates a corpus.
    """
    if not paginate and not _is_index(path):
        return _plan_document(path, lines)
    text = _render(lines).decode("utf-8")
    updates = store.plan(path, text, as_of=as_of, cold_days=cold_days)
    if updates:
        _verify_archive_candidate(store, path, updates, text)
    return updates


def _plan_document(path: Path, lines: Sequence[str]) -> dict[Path, bytes | None]:
    """Return the write for one plain managed document, or nothing.

    Drift is decided on decoded lines, never on raw bytes. A checkout with
    `core.autocrlf` on holds the same documents with CRLF endings, and a byte
    comparison against this tool's LF output would call every such file
    drifted on every run -- a rewrite loop that no edit could ever settle.
    """
    if _read_lines_optional(path) == list(lines):
        return {}
    return {path: _render(lines)}


def _plan_text(path: Path, text: str) -> dict[Path, bytes | None]:
    """Return the write for one document that was planned as whole text.

    ``splitlines`` rather than ``split("\\n")``: a text ending in a newline
    splits to a trailing empty element that the renderer then strips, so the
    planned lines would never equal the lines read back and the document
    would be reported as drifted on every run.
    """
    return _plan_document(path, text.splitlines())


#: Where an existing `[test_count]` table's own heading line sits.
_TEST_COUNT_TABLE_RE = re.compile(r"^\[test_count\]\s*$", re.MULTILINE)
#: The `pinned =` line inside that table, however it is indented.
_TEST_COUNT_PINNED_LINE_RE = re.compile(r"^\s*pinned\s*=.*$", re.MULTILINE)


def _rewrite_test_count_pin(text: str, count: int) -> str:
    """Return config/docsync.toml's text with `[test_count]` pinned to count.

    A targeted find-or-append of one line, not a general TOML writer,
    because the stdlib `tomllib` this repository already relies on is
    read-only and no new dependency is allowed. Replaces an existing
    `[test_count]` table's `pinned =` line in place, or inserts one right
    after the table heading when the table exists but carries no pin yet.
    Appends a new `[test_count]\\npinned = N\\n` block at the end of the
    file's text when the table is absent entirely -- never between existing
    `[[value]]` blocks, since a single-bracket table opens and closes no
    array scope but a wrong insertion point beside one has bitten this file
    before (F-DOCSYNC-8's scoping notice).
    """
    table_match = _TEST_COUNT_TABLE_RE.search(text)
    if table_match is None:
        if not text.strip():
            return f"[test_count]\npinned = {count}\n"
        prefix = text if text.endswith("\n") else text + "\n"
        if not prefix.endswith("\n\n"):
            prefix += "\n"
        return f"{prefix}[test_count]\npinned = {count}\n"

    header_end = table_match.end()
    body_start = (
        header_end + 1 if text[header_end : header_end + 1] == "\n" else header_end
    )
    next_heading = re.search(r"^\[", text[body_start:], re.MULTILINE)
    body_end = body_start + next_heading.start() if next_heading else len(text)
    body = text[body_start:body_end]

    pinned_match = _TEST_COUNT_PINNED_LINE_RE.search(body)
    if pinned_match is not None:
        new_body = (
            body[: pinned_match.start()]
            + f"pinned = {count}"
            + body[pinned_match.end() :]
        )
    else:
        new_body = f"pinned = {count}\n" + body
    return text[:body_start] + new_body + text[body_end:]


def _rewrite_findings_header_count(text: str, count: int) -> str:
    """Return FINDINGS.md's text with its header test-count line rewritten.

    Mirrors `_check_findings_header_count`'s own header-boundary rule
    (`_FINDINGS_HEADER_END_RE`, the first heading line) so the writer and
    the DOC008 checker agree on where "the header" ends -- a count quoted
    in running prose below the header is never touched.
    """
    lines = text.splitlines()
    header_end = len(lines)
    for line_number, line in enumerate(lines, start=1):
        if line_number > 1 and _FINDINGS_HEADER_END_RE.match(line):
            header_end = line_number - 1
            break
    new_lines = (
        rewrite_recorded_counts(lines[:header_end], count, [FINDINGS_HEADER_COUNT_RE])
        + lines[header_end:]
    )
    return "\n".join(new_lines) + "\n"


def _publish(
    updates: Mapping[Path, bytes | None], expected: Mapping[Path, bytes | None]
) -> None:
    """Publish one transaction against the repository root."""
    publish(_repo_root(), updates, expected)


# ---------------------------------------------------------------------- #
# Drift                                                                   #
# ---------------------------------------------------------------------- #


def _drift_updates(
    corpus: _Corpus,
    result,
    rotation: findings_module.FindingRotation,
    explicit_test_count: int | None = None,
) -> dict[Path, bytes | None]:
    """Return every write the deterministic renderer and rotation would make."""
    store = corpus.store
    config = load_archive_config(REPO_ROOT, config_path=CONFIG_PATH)
    documents = _documents()
    updates: dict[Path, bytes | None] = {}
    updates.update(
        _plan_document(REPO_ROOT / documents.playbook, result.playbook_lines)
    )
    updates.update(
        _plan_archive(
            store,
            ARCHIVE_PATH,
            result.archive_lines,
            cold_days=config.cold_days,
            paginate=False,
        )
    )
    for batch_num, batch_lines in result.batch_log_updates.items():
        updates.update(
            _plan_archive(
                store,
                _get_batch_log_path(batch_num),
                batch_lines,
                cold_days=config.cold_days,
                paginate=False,
            )
        )
    if (
        result.session_lines is not None
        and corpus.session_lines != result.session_lines
    ):
        updates.update(_plan_document(SESSION_CONTEXT_PATH, result.session_lines))
    if rotation.rotated_ids:
        updates.update(_plan_text(REPO_ROOT / documents.findings, rotation.active_text))
        updates.update(
            _plan_archive(
                store,
                FINDINGS_ARCHIVE_PATH,
                rotation.archive_text.splitlines(),
                cold_days=config.cold_days,
                paginate=False,
            )
        )
    if explicit_test_count is not None:
        # An operator has just asserted the true count with --test-count: pin
        # it in config/docsync.toml and rewrite the FINDINGS.md header from
        # it, the two sites SESSION_CONTEXT's rewrite pass above does not
        # reach. rewrite_recorded_counts already covers the STATUS block, the
        # Section 1 Tests row and the Section 6 heading inside `_sync` itself.
        findings_text = (
            rotation.active_text if rotation.rotated_ids else corpus.findings_text
        )
        new_findings_text = _rewrite_findings_header_count(
            findings_text, explicit_test_count
        )
        updates.update(_plan_text(REPO_ROOT / documents.findings, new_findings_text))

        declarations_text = (
            corpus.declarations_path.read_text(encoding="utf-8")
            if corpus.declarations_path.is_file()
            else ""
        )
        new_declarations_text = _rewrite_test_count_pin(
            declarations_text, explicit_test_count
        )
        updates.update(_plan_text(corpus.declarations_path, new_declarations_text))
    return updates


def _archive_page_target_issues(store: ArchiveStore) -> list[IntegrityIssue]:
    """DOC024 diagnostics across every managed archive (warning severity).

    Every archive `--paginate-archives` and `--cold-storage` would touch is
    checked here too, so `--check` reports the same page-target health those
    explicit maintenance commands would act on -- without ever running them.
    """
    issues: list[IntegrityIssue] = []
    for path in _managed_archive_paths():
        issues.extend(store.page_target_issues(path))
    return issues


def _collect_issues(
    corpus: _Corpus,
    result,
    rotation: findings_module.FindingRotation,
) -> list[IntegrityIssue]:
    """Collect every blocking diagnostic for the corpus as it stands."""
    documents = _documents()
    return [
        *corpus.issues,
        *rotation.issues,
        *_archive_page_target_issues(corpus.store),
        *collect_integrity_issues(
            repo_root=REPO_ROOT,
            live_documents=corpus.live_documents,
            playbook_lines=corpus.playbook_lines,
            archive_lines=corpus.archive_lines,
            session_lines=corpus.session_lines,
            expected_session_lines=result.session_lines,
            tracked_paths=corpus.tracked_paths,
            batch_log_lines=corpus.batch_log_lines,
            config_path=CONFIG_PATH,
            document_paths=resolved_live_document_paths(documents),
            playbook_relative_path=documents.playbook,
            findings_relative_path=documents.findings,
        ),
    ]


def _report(issues: Sequence[IntegrityIssue]) -> bool:
    """Print every diagnostic and the root-file warnings; say if any blocks."""
    for issue in issues:
        print(_format_issue(issue), file=sys.stderr)
    for warning in _check_root_batch_files(REPO_ROOT):
        print(f"WARNING: {warning}", file=sys.stderr)
    return any(issue.severity == "error" for issue in issues)


def _sync_corpus(
    corpus: _Corpus, keep_non_current: int, explicit_test_count: int | None = None
):
    """Run the deterministic renderer over one already-read corpus."""
    config = load_test_count_config(REPO_ROOT, config_path=CONFIG_PATH)
    return _sync(
        playbook_lines=corpus.playbook_lines,
        archive_lines=corpus.archive_lines,
        session_lines=corpus.session_lines,
        keep_non_current=keep_non_current,
        batch_log_lines=corpus.batch_log_lines,
        planned_wp_numbers=_read_active_planned_wp_numbers(corpus.playbook_lines),
        pinned=config.pinned,
        explicit_test_count=explicit_test_count,
    )


# ---------------------------------------------------------------------- #
# --close-batch                                                           #
# ---------------------------------------------------------------------- #


def _root_definition_candidates(batch: int, tracked_paths: frozenset[str]) -> list[str]:
    """Return the tracked root definitions that name this batch."""
    candidate_re = root_definition_pattern(batch)
    return sorted(
        path
        for path in tracked_paths
        if "/" not in path and candidate_re.fullmatch(path) is not None
    )


def _purge_current_batch_window(playbook_lines: list[str]) -> list[str]:
    """Move Section 4's current-batch entries out of the active window.

    The window holds the entries of the batch that is ending. While they sit
    between the markers the renderer reads them as the active batch's work and
    keeps them in PLAYBOOK indefinitely, because no other signal tells it the
    batch is over. Relocating them below the end marker hands them to the
    ordinary rotation rules the renderer already has: a tagged entry goes to
    its own per-batch log, an untagged side-task entry falls under the
    retention window like any other. Nothing is dropped, and nothing about
    the entries themselves is rewritten.
    """
    section_start, section_end = _find_section(
        playbook_lines, SECTION_4_RE, "PLAYBOOK section 4"
    )
    section = playbook_lines[section_start:section_end]
    marker_start, marker_end = _find_marker_pair(
        section,
        CURRENT_BATCH_START_MARKER,
        CURRENT_BATCH_END_MARKER,
        "PLAYBOOK section 4",
    )
    entries, _ = _parse_entries(section)
    inside = [entry for entry in entries if marker_start < entry.start_idx < marker_end]
    if not inside:
        return list(playbook_lines)

    # An entry's parsed block runs to the next entry or the end of the
    # window, so the last one carries the end marker with it. Stripping
    # marker lines here is what keeps the relocated block from planting a
    # second end marker below the first.
    moved: list[str] = []
    for entry in inside:
        moved.append("")
        moved.extend(_trim_trailing_blank(_remove_marker_lines(entry.lines)))
    new_section = (
        section[: marker_start + 1]
        + ["", section[marker_end]]
        + moved
        + section[marker_end + 1 :]
    )
    return playbook_lines[:section_start] + new_section + playbook_lines[section_end:]


def _candidate_live_documents(
    corpus: _Corpus,
    *,
    playbook_lines: list[str],
    findings_text: str,
    source_relative: str,
    archived_relative: str,
    archived_lines: list[str],
) -> dict[str, list[str]]:
    """Return the live documents as the transition would leave them.

    Validating the candidate from disk would grade the documents the closure
    is about to replace, which is exactly the state it is trying to leave: the
    definition still at the root, the index still pointing there. The archived
    definition is supplied here for the same reason it is supplied on an
    ordinary check -- it is a document the gate reads, and a declaration may
    name it.
    """
    document_paths = _documents()
    live_documents = dict(corpus.live_documents)
    live_documents.pop(source_relative, None)
    live_documents[archived_relative] = archived_lines
    live_documents[_repository_relative(REPO_ROOT / document_paths.playbook)] = (
        playbook_lines
    )
    live_documents[_repository_relative(REPO_ROOT / document_paths.findings)] = (
        findings_text.split("\n")
    )
    return live_documents


def _resolve_closed_on(batch: int, archived_relative: str, proposed: str) -> str:
    """Return the date this batch's closure is recorded under.

    A batch is closed once, and the date its record already carries is the
    audit trail the command exists to write. A second close -- a retried job,
    or an operator who does not recall the first -- must not restate when the
    closure happened, least of all from today's clock. The first record wins,
    and a conflicting ``--as-of`` is reported rather than applied, so
    correcting a date stays a deliberate edit.

    The record is read from the archived definition by path, never from the
    lines the close was built from: that source is the *root* definition
    whenever one is tracked, and a root restored after a close carries no
    record at all, which would hand the date back to the clock.
    """
    archived_existing = _read_lines_optional(REPO_ROOT / archived_relative)
    if archived_existing is None:
        return proposed
    recorded = read_closeout_record(archived_existing)
    if recorded is None:
        return proposed
    if recorded.closed_on != proposed:
        print(
            f"doc_state_sync --close-batch {batch}: batch {batch} is already "
            f"recorded as closed on {recorded.closed_on}; keeping that date "
            f"and ignoring {proposed}.",
            file=sys.stderr,
        )
    return recorded.closed_on


def _close_batch(batch: int, keep_non_current: int, closed_on: str) -> int:
    """Perform the whole batch transition, or refuse and write nothing.

    Validation runs in two passes for two different reasons. The first asks
    whether the author's evidence is in place -- the PLAYBOOK claim, the work
    package dispositions, the dashboard, the index row, the finding records --
    and refuses when it is not, because none of that is the tool's to write.
    The second grades the corpus the transition would produce, so a closure
    cannot publish documents that fail the ordinary gate. Only then is
    anything written, and then all of it at once.
    """
    store = _archive_store()
    corpus = _Corpus(store)
    if corpus.issues:
        _report(corpus.issues)
        return 1

    documents = _documents()
    config = load_closeout_config(REPO_ROOT, config_path=CONFIG_PATH)
    archive_config = load_archive_config(REPO_ROOT, config_path=CONFIG_PATH)
    archived_relative = f"{ARCHIVED_DEFINITIONS_DIR}BATCH{batch}_DEFINITION.md"
    roots = _root_definition_candidates(batch, corpus.tracked_paths)
    source_relative = roots[0] if roots else archived_relative
    source_path = REPO_ROOT / source_relative
    definition_lines = _read_lines_optional(source_path)

    rotation = corpus.rotation()
    issues = [
        *collect_transition_issues(
            batch=batch,
            playbook_lines=corpus.playbook_lines,
            session_lines=corpus.session_lines,
            session_path=_repository_relative(SESSION_CONTEXT_PATH),
            definition_path=source_relative,
            definition_lines=definition_lines,
            tracked_paths=corpus.tracked_paths,
            config=config,
            playbook_relative_path=documents.playbook,
        ),
        *rotation.issues,
    ]
    if issues:
        _report(issues)
        print(
            f"doc_state_sync --close-batch {batch} refused: the close-out "
            f"evidence above is missing or contradictory. Nothing was written.",
            file=sys.stderr,
        )
        return 1
    if definition_lines is None:
        # Not an assert: `python -O` strips those, and this one stands
        # between a missing definition and a publish that would write the
        # close-out record from nothing.
        raise SyncError(
            f"close-out for batch {batch} reported no issues but produced no "
            f"definition to archive; refusing to publish."
        )

    closed_on = _resolve_closed_on(batch, archived_relative, closed_on)

    archived_lines = render_archived_definition(definition_lines, batch, closed_on)
    playbook_lines = _purge_current_batch_window(list(corpus.playbook_lines))
    row = find_batch_index_row(playbook_lines, batch)
    if row is None:
        raise SyncError(
            f"{documents.playbook} has no batch index row for batch {batch} "
            f"after the close-out checks passed; refusing to publish."
        )
    playbook_lines[row] = render_batch_index_row(
        playbook_lines[row],
        archived_relative,
        _get_batch_log_path(batch).as_posix(),
    )
    corpus.playbook_lines = playbook_lines
    result = _sync_corpus(corpus, keep_non_current)

    candidate_batch_logs = dict(corpus.batch_log_lines)
    candidate_batch_logs.update(result.batch_log_updates)
    candidate_tracked = (corpus.tracked_paths - {source_relative}) | {
        archived_relative,
        _repository_relative(FINDINGS_ARCHIVE_PATH),
    }
    candidate_issues = collect_integrity_issues(
        repo_root=REPO_ROOT,
        live_documents=_candidate_live_documents(
            corpus,
            playbook_lines=result.playbook_lines,
            findings_text=rotation.active_text,
            source_relative=source_relative,
            archived_relative=archived_relative,
            archived_lines=archived_lines,
        ),
        playbook_lines=result.playbook_lines,
        archive_lines=result.archive_lines,
        session_lines=result.session_lines,
        expected_session_lines=result.session_lines,
        tracked_paths=candidate_tracked,
        batch_log_lines=candidate_batch_logs,
        config_path=CONFIG_PATH,
        document_paths=resolved_live_document_paths(documents),
        playbook_relative_path=documents.playbook,
        findings_relative_path=documents.findings,
    )
    if any(issue.severity == "error" for issue in candidate_issues):
        _report(candidate_issues)
        print(
            f"doc_state_sync --close-batch {batch} refused: the corpus this "
            f"closure would publish does not pass the gate. Nothing was written.",
            file=sys.stderr,
        )
        return 1

    updates: dict[Path, bytes | None] = {}
    updates.update(_plan_document(REPO_ROOT / archived_relative, archived_lines))
    if source_relative != archived_relative:
        updates[source_path] = None
    updates.update(
        _plan_document(REPO_ROOT / documents.playbook, result.playbook_lines)
    )
    updates.update(
        _plan_archive(
            store,
            ARCHIVE_PATH,
            result.archive_lines,
            cold_days=archive_config.cold_days,
            paginate=False,
        )
    )
    for batch_num, batch_lines in result.batch_log_updates.items():
        updates.update(
            _plan_archive(
                store,
                _get_batch_log_path(batch_num),
                batch_lines,
                cold_days=archive_config.cold_days,
                paginate=False,
            )
        )
    if result.session_lines is not None:
        updates.update(_plan_document(SESSION_CONTEXT_PATH, result.session_lines))
    if rotation.rotated_ids:
        updates.update(_plan_text(REPO_ROOT / documents.findings, rotation.active_text))
        updates.update(
            _plan_archive(
                store,
                FINDINGS_ARCHIVE_PATH,
                rotation.archive_text.splitlines(),
                cold_days=archive_config.cold_days,
                paginate=False,
            )
        )

    # `corpus.read_paths()` is the single source of truth for "what did this
    # run read": every live document, both archives' members, and every
    # batch log's members, derived from the corpus object itself rather than
    # a hand-maintained list that could fall behind it. `source_path` is
    # listed explicitly too, since a batch closing for the first time reads
    # its own root definition, which is also about to be deleted here.
    sources = [source_path, *corpus.read_paths()]
    _publish(updates, _preimages([*sources, *updates]))

    if not updates:
        print(f"doc_state_sync --close-batch {batch}: already closed; no changes.")
        return 0
    print(f"doc_state_sync --close-batch {batch} published:")
    for path in sorted(updates):
        verb = "removed" if updates[path] is None else "wrote"
        print(f"- {verb} {path}")
    if rotation.rotated_ids:
        print(f"- rotated findings: {', '.join(rotation.rotated_ids)}")
    return 0


# ---------------------------------------------------------------------- #
# --split-archive                                                         #
# ---------------------------------------------------------------------- #


def _split_archive_mode() -> int:
    """Migrate the monolith archive into per-batch log files, as one transaction.

    This is a one-time migration, not ordinary drift repair, but it writes
    the same repository history every other mode writes and must be exactly
    as safe: it takes the single-writer lock, so it can never race a
    concurrent `--fix` or `--close-batch` that already holds it; it proves
    every file it read is still byte-identical right before it writes, so an
    edit landing after this run planned its work cannot be silently
    overwritten; and it publishes every per-batch log and the trimmed
    monolith in one journaled transaction, so a crash partway through can
    never leave an entry duplicated in both places, or removed from the
    monolith before it exists anywhere else.
    """
    archive_lines = _read_lines(ARCHIVE_PATH)
    remaining_lines, batch_groups = _split_archive(archive_lines)

    updates: dict[Path, bytes | None] = {}
    sources: list[Path] = [ARCHIVE_PATH]
    for batch_num, new_entries in sorted(batch_groups.items()):
        batch_log_path = _get_batch_log_path(batch_num)
        sources.append(batch_log_path)
        existing = _read_lines_optional(batch_log_path) or []
        merged = _merge_entries_into_log(existing, new_entries, batch_num)
        updates.update(_plan_document(batch_log_path, merged))

    updates.update(_plan_document(ARCHIVE_PATH, remaining_lines))

    _publish(updates, _preimages([*sources, *updates]))

    if updates:
        print("doc_state_sync --split-archive wrote:")
        for path in sorted(updates):
            print(f"- {path}")
    else:
        print("doc_state_sync --split-archive: no changes needed.")
    print(
        f"doc_state_sync --split-archive summary: "
        f"{len(batch_groups)} batch(es) found, "
        f"{len(updates)} file(s) written."
    )
    return 0


# ---------------------------------------------------------------------- #
# --paginate-archives and --cold-storage                                  #
# ---------------------------------------------------------------------- #


def _managed_archive_paths() -> list[Path]:
    """Return every archive entry point this repository maintains."""
    paths = [ARCHIVE_PATH, FINDINGS_ARCHIVE_PATH]
    if LOGS_DIR.exists():
        paths.extend(_batch_filename_candidates(LOGS_DIR, _BATCH_LOG_RE))
    return [path for path in paths if path.is_file()]


def _maintain_archives(*, as_of: dt.date | None, label: str) -> int:
    """Run one explicit archive maintenance pass over every managed archive.

    Pagination and cold aging are the same operation with one difference:
    whether an as-of date is supplied. Keeping them in one function is what
    guarantees that a cold run also honours the page target and a pagination
    run never ages anything, because neither can drift from the other.
    """
    store = _archive_store()
    config = load_archive_config(REPO_ROOT, config_path=CONFIG_PATH)
    updates: dict[Path, bytes | None] = {}
    sources: list[Path] = []
    issues: list[IntegrityIssue] = []

    for path in _managed_archive_paths():
        text, issue = _archive_text(store, path)
        if issue is not None:
            issues.append(issue)
            continue
        sources.extend(_archive_members(path))
        planned = store.plan(path, text, as_of=as_of, cold_days=config.cold_days)
        if planned:
            _verify_archive_candidate(store, path, planned, text)
        updates.update(planned)

    if issues:
        _report(issues)
        print(
            f"doc_state_sync {label} refused: repair the archive layout above "
            f"first. Nothing was written.",
            file=sys.stderr,
        )
        return 1

    _publish(updates, _preimages([*sources, *updates]))
    if not updates:
        print(f"doc_state_sync {label}: no changes needed.")
        return 0
    print(f"doc_state_sync {label} published:")
    for path in sorted(updates):
        verb = "removed" if updates[path] is None else "wrote"
        print(f"- {verb} {path}")
    return 0


# ---------------------------------------------------------------------- #
# Argument handling                                                       #
# ---------------------------------------------------------------------- #


def _parse_as_of(raw: str) -> dt.date:
    """Read a strict ISO maintenance date, refusing every other spelling."""
    if _ISO_DATE_RE.match(raw) is None:
        raise SyncError(f"--as-of must be written as YYYY-MM-DD, not {raw!r}.")
    try:
        return dt.date.fromisoformat(raw)
    except ValueError:
        raise SyncError(f"--as-of {raw!r} is not a real calendar date.") from None


def _build_parser() -> argparse.ArgumentParser:
    """Declare every mode and option the entry point accepts."""
    parser = argparse.ArgumentParser(
        description="Sync PLAYBOOK/SESSION_CONTEXT/archive state deterministically."
    )
    parser.add_argument(
        "--check", action="store_true", help="Validate state only (no file writes)."
    )
    parser.add_argument(
        "--fix", action="store_true", help="Apply deterministic state updates to files."
    )
    parser.add_argument(
        "--split-archive",
        action="store_true",
        help=(
            "One-time migration: split the monolith archive into per-batch log files. "
            "Mutually exclusive with --check and --fix."
        ),
    )
    parser.add_argument(
        "--close-batch",
        type=int,
        metavar="N",
        help=(
            "Close batch N: validate every close-out signal, then archive the "
            "definition, repoint the index, rotate and refresh, as one transaction."
        ),
    )
    parser.add_argument(
        "--paginate-archives",
        action="store_true",
        help="Migrate oversized archives to indexed, numbered pages.",
    )
    parser.add_argument(
        "--cold-storage",
        action="store_true",
        help=(
            "Move finalized, fully aged archive pages beneath cold/. "
            "Requires an explicit --as-of date."
        ),
    )
    parser.add_argument(
        "--as-of",
        metavar="YYYY-MM-DD",
        help=(
            "The explicit maintenance date. Required by --cold-storage, which "
            "never reads the wall clock; optional for --close-batch, where it "
            "dates the close-out record."
        ),
    )
    parser.add_argument(
        "--keep-non-current",
        type=int,
        default=4,
        help="How many non-current entries to keep in PLAYBOOK section 4 (default: 4).",
    )
    parser.add_argument(
        "--test-count",
        type=int,
        metavar="N",
        help=(
            "The measured `pytest -q` result. Valid only with --fix: pins N in "
            "config/docsync.toml's [test_count] table and writes the STATUS "
            "block, the SESSION_CONTEXT Section 1 Tests row, the Section 6 "
            "heading and the FINDINGS.md header from it, in one command."
        ),
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help=(
            "Path inside the repository to the declarations file, overriding the default "
            f"({DECLARATIONS_FILENAME})."
        ),
    )
    return parser


def main() -> int:
    global CONFIG_PATH
    parser = _build_parser()
    args = parser.parse_args()
    previous_config_path = CONFIG_PATH
    CONFIG_PATH = Path(args.config) if args.config is not None else None
    try:
        modes = [
            args.check,
            args.fix,
            args.split_archive,
            args.close_batch is not None,
            args.paginate_archives,
            args.cold_storage,
        ]
        if sum(bool(mode) for mode in modes) > 1:
            print(
                "Use exactly one mode: --check, --fix, --split-archive, "
                "--close-batch, --paginate-archives, or --cold-storage.",
                file=sys.stderr,
            )
            return 2

        if not any(modes):
            print("No mode selected; defaulting to --check.", file=sys.stderr)
            args.check = True

        if args.keep_non_current < 0:
            print("--keep-non-current must be >= 0.", file=sys.stderr)
            return 2

        if args.test_count is not None:
            if not args.fix:
                print("--test-count requires --fix.", file=sys.stderr)
                return 2
            if args.test_count < 0:
                print("--test-count must be >= 0.", file=sys.stderr)
                return 2

        as_of: dt.date | None = None
        if args.as_of is not None:
            if not (args.cold_storage or args.close_batch is not None):
                print(
                    "--as-of only applies to --cold-storage and --close-batch.",
                    file=sys.stderr,
                )
                return 2
            try:
                as_of = _parse_as_of(args.as_of)
            except SyncError as exc:
                print(f"doc_state_sync failed: {exc}", file=sys.stderr)
                return 2
        if args.cold_storage and as_of is None:
            print(
                "--cold-storage requires --as-of YYYY-MM-DD. Ageing history from "
                "the wall clock would move files because a day passed, not because "
                "a maintainer decided to.",
                file=sys.stderr,
            )
            return 2

        # ------------------------------------------------------------------ #
        # --split-archive mode                                                 #
        # ------------------------------------------------------------------ #
        if args.split_archive:
            try:
                return _split_archive_mode()
            except SyncError as exc:
                print(f"doc_state_sync failed: {exc}", file=sys.stderr)
                return 2

        # ------------------------------------------------------------------ #
        # Archive maintenance modes                                            #
        # ------------------------------------------------------------------ #
        if args.paginate_archives or args.cold_storage:
            label = "--cold-storage" if args.cold_storage else "--paginate-archives"
            try:
                return _maintain_archives(as_of=as_of, label=label)
            except SyncError as exc:
                print(f"doc_state_sync failed: {exc}", file=sys.stderr)
                return 2

        # ------------------------------------------------------------------ #
        # --close-batch mode                                                   #
        # ------------------------------------------------------------------ #
        if args.close_batch is not None:
            # The record states when the closure was performed, which is today
            # unless the operator says otherwise. This is the one place a date is
            # read from the clock, and it is safe precisely because it decides
            # nothing: no file moves or ages because of it. Cold storage, which
            # does move files by date, refuses the clock outright.
            closed_on = (as_of or dt.date.today()).isoformat()
            try:
                return _close_batch(args.close_batch, args.keep_non_current, closed_on)
            except SyncError as exc:
                print(f"doc_state_sync failed: {exc}", file=sys.stderr)
                return 2

        # ------------------------------------------------------------------ #
        # --check / --fix modes                                                #
        # ------------------------------------------------------------------ #
        try:
            store = _archive_store()
            corpus = _Corpus(store)
            # An archive whose pages and index disagree is reported, never acted
            # on. Planning against it would write the half of the corpus the
            # reader could still see over the half it could not.
            if corpus.issues:
                _report(corpus.issues)
                return 1
            result = _sync_corpus(
                corpus, args.keep_non_current, explicit_test_count=args.test_count
            )
            rotation = corpus.rotation()
            updates = _drift_updates(
                corpus, result, rotation, explicit_test_count=args.test_count
            )
        except SyncError as exc:
            print(f"doc_state_sync failed: {exc}", file=sys.stderr)
            return 2

        if args.check:
            try:
                issues = _collect_issues(corpus, result, rotation)
            except SyncError as exc:
                print(f"doc_state_sync failed: {exc}", file=sys.stderr)
                return 2
            blocking = _report(issues)
            if updates:
                print("doc_state_sync drift detected:")
                for path in sorted(updates):
                    print(f"- {path}")
                print("Run: python scripts/doc_state_sync.py --fix")
            if updates or blocking:
                return 1
            print(
                "doc_state_sync check passed "
                f"(current_batch_entries={result.current_batch_entry_count}, "
                f"kept_non_current={result.kept_non_current_count}, "
                f"rotated={result.rotated_count})."
            )
            return 0

        # args.fix: publish the deterministic renderer output and the eligible
        # rotation as one transaction, then validate the resulting disk state.
        # Semantic integrity issues remain for a human fix, exactly as before:
        # refusing to repair drift because an unrelated document has a dead
        # reference would leave the repository with two defects instead of one.
        try:
            if updates:
                # See `_close_batch`'s identical comment: `corpus.read_paths()`
                # covers every live document and every archive's members
                # (including batch logs that were only read, not rewritten,
                # in this run) so the staleness check cannot miss a source.
                _publish(updates, _preimages([*corpus.read_paths(), *updates]))
                print("doc_state_sync wrote updates:")
                for path in sorted(updates):
                    print(f"- {path}")
            else:
                print("doc_state_sync --fix found no changes.")

            final_corpus = _Corpus(store)
            final_result = _sync_corpus(
                final_corpus, args.keep_non_current, explicit_test_count=args.test_count
            )
            final_rotation = final_corpus.rotation()
            final_updates = _drift_updates(
                final_corpus,
                final_result,
                final_rotation,
                explicit_test_count=args.test_count,
            )
            issues = _collect_issues(final_corpus, final_result, final_rotation)
        except SyncError as exc:
            print(f"doc_state_sync failed: {exc}", file=sys.stderr)
            return 2
        blocking = _report(issues)
        if final_updates or blocking:
            return 1

        print(
            "doc_state_sync summary "
            f"(current_batch_entries={result.current_batch_entry_count}, "
            f"kept_non_current={result.kept_non_current_count}, "
            f"rotated={result.rotated_count})."
        )
        return 0
    finally:
        CONFIG_PATH = previous_config_path
