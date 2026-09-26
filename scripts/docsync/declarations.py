"""Deterministic checks for facts that are written down more than once.

Six of Batch 21's first nineteen review comments were not logic defects. They
were one fact recorded in several places, where the copies had drifted: a
breakpoint that differed between a stylesheet and a script, a reversed
decision still prescribed by five documents, a test count, a checkpoint, and a
cross-reference to a rule that had moved. `F-B21-17` has the tally.

A written rule cannot close that class. `AGENTS.md` already said to cite by
name rather than by line number, and the citation that broke *was* by name --
the name itself moved, in the same commit. Only something that resolves the
reference can catch that.

Three checks, all reading from one declarations file so the mechanism carries
to another repository unchanged and only the declarations are local:

- **DOC009** -- a value written in several places still agrees with itself.
- **DOC010** -- a cross-reference resolves to something that exists.
- **DOC011** -- a claim that has been retired does not survive in a document
  that still prescribes behaviour.

The declarations file is TOML, read with the standard library, so this adds no
dependency.
"""

from __future__ import annotations

import dataclasses
import fnmatch
import re
from collections import namedtuple
from collections.abc import Iterable, Mapping
from pathlib import Path, PureWindowsPath

import tomllib

from docsync.markdown import fully_struck, marker_lines, prose_lines
from docsync.models import IntegrityIssue, SyncError
from docsync.transaction import resolve_within

#: Where the repository's own declarations live, relative to the repo root.
DECLARATIONS_FILENAME = "config/docsync.toml"

#: A heading in a Markdown document: one to six hashes, then the text.
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")

#: An ordered-list item at the start of a line: "3. **Something**".
_LIST_ITEM_RE = re.compile(r"^(\d+)\.\s")

#: A bold lead-in used as a section marker: "**Wordmark animation** ...".
#: docs/design/README.md labels its sections this way rather than with
#: hashes, and a citation of one is a citation of a real place in the file.
#:
#: The list bullet is optional because that document labels sections both
#: ways. "- **Responsive.** Single breakpoint." is a section of it,
#: and a citation of "Responsive" resolved nowhere while this pattern
#: insisted the asterisks start the line.
_BOLD_LABEL_RE = re.compile(r"^\s*(?:[-*+]\s+)?\*\*([^*]+?)\*\*")

#: A trailing parenthetical on a heading: "Session Bootstrap (in order)".
#: Citations routinely leave it off, and that is not a broken reference.
_HEADING_SUFFIX_RE = re.compile(r"\s*\([^()]*\)\s*$")

#: Where a section label stops being a name and starts being a sentence:
#: "Wordmark animation -- read this before touching the logo." A citation
#: names the label, never the sentence after it.
_LABEL_TAIL_RE = re.compile(r"\s*(?:--|—|:)\s.*$")

#: Text struck through in Markdown.
#:
#: Treating ~~this~~ as "no longer current" is a convention, not a rule of the
#: language. It holds in this repository, where strikethrough is only ever used
#: to keep a superseded step visible beside its reversal. Somewhere else it may
#: be rhetorical -- "~~bugs~~ features" -- and exempting it there would hand a
#: retired claim an invisibility cloak. So the exemption is a declared option
#: rather than doctrine baked into the tool: `[options] strikethrough_exempt`
#: sets the default, and any [[retired]] declaration can override it.

#: What `strikethrough_exempt` defaults to when nothing declares it. On,
#: because it matches the convention most Markdown corpora follow -- but the
#: option exists so a corpus that does not follow it can say so.
DEFAULT_STRIKETHROUGH_EXEMPT = True

#: What `[archives] max_lines` defaults to: the rendered-line target for one
#: archive page. Large enough that an ordinary batch's log stays one file,
#: which is why a repository that never paginates needs no table at all.
DEFAULT_ARCHIVE_MAX_LINES = 500

#: What `[archives] cold_days` defaults to: the age at which a finalized page
#: becomes eligible to move beneath `cold/`. Only an explicit as-of date ever
#: evaluates it, so this value cannot age a file on its own.
DEFAULT_ARCHIVE_COLD_DAYS = 365

#: What `[closeout] admit_from_batch` defaults to: the lowest batch number
#: whose closure the close-out signals are evaluated against. Every batch at or
#: above the boundary is managed, so a batch cannot opt out of the check by
#: being absent from a list -- which is why the boundary is an integer rather
#: than a recorded set.
#:
#: The default is the strict end of the range, not the permissive one. A
#: repository that adopted this tooling from its first batch wants every closure
#: checked, and "no table" must not be readable as "no batch is managed". A
#: repository with older history overrides the value to grandfather batches
#: that closed before the signals existed, because requiring those to be
#: rewritten would be fabricating evidence.
DEFAULT_CLOSEOUT_ADMIT_FROM_BATCH = 1


class DeclarationError(SyncError):
    """The declarations file itself is wrong, so no check could run.

    Kept separate from a check failing. A malformed declaration is a defect in
    the gate, and reporting it as a document problem would send the reader to
    edit the wrong file. The distinct class and message keep that separation.

    It is a SyncError so the CLI reports it the documented way and exits 2.
    Raising a type the CLI had never heard of ended the run in a traceback and
    exit 1, which reads as "the gate crashed" rather than "the declarations
    file has a typo, and here is the line".
    """


#: A declared type. A plain type where the value stands alone, or one of these
#: two where it is a container: what a container holds has to be right as well.
#: `scan = [1]` is a list, and reaches `_expand` as a TypeError.
_ListOf = namedtuple("_ListOf", "element minimum", defaults=(0,))
_MappingOf = namedtuple("_MappingOf", "key value")


def _describe(spec: object) -> str:
    """Name a declared type the way the file's author would write it."""
    if isinstance(spec, _ListOf):
        if spec.minimum:
            return f"a list of at least {spec.minimum} {spec.element.__name__}"
        return f"a list of {spec.element.__name__}"
    if isinstance(spec, _MappingOf):
        return f"a table of {spec.key.__name__} to {spec.value.__name__}"
    return spec.__name__  # type: ignore[union-attr]


def _mismatch(spec: object, value: object) -> str | None:
    """Say how a value fails its declared type, or None when it fits.

    Checks inside a container, not only the container. A shallow check
    accepted `scan = [1]` and `allow_after = {"PLAYBOOK.md" = 5}`, which then
    raised TypeError somewhere far from the declaration that caused it.
    """
    if isinstance(spec, _ListOf):
        if not isinstance(value, list):
            return f"{type(value).__name__}, not {_describe(spec)}"
        if len(value) < spec.minimum:
            seen = "an empty list" if not value else f"a list of {len(value)}"
            return f"{seen}, not {_describe(spec)}"
        for position, item in enumerate(value):
            if not isinstance(item, spec.element):
                return (
                    f"a list whose item {position} is {type(item).__name__}, "
                    f"not {spec.element.__name__}"
                )
        return None
    if isinstance(spec, _MappingOf):
        if not isinstance(value, Mapping):
            return f"{type(value).__name__}, not {_describe(spec)}"
        for key, held in value.items():
            if not isinstance(key, spec.key):
                return (
                    f"a table with a {type(key).__name__} key, not {spec.key.__name__}"
                )
            if not isinstance(held, spec.value):
                return (
                    f"a table whose {key!r} is {type(held).__name__}, "
                    f"not {spec.value.__name__}"
                )
        return None
    if not isinstance(value, spec):  # type: ignore[arg-type]
        return f"{type(value).__name__}, not {_describe(spec)}"
    return None


#: What a declaration of each kind may hold, and what type each key takes.
#:
#: Every key is listed rather than only the required ones, because the worst
#: way a declarations file can be wrong is quietly. A misspelled `scans` left
#: the declaration scanning nothing and the gate green, which is the exact
#: failure this whole module exists to prevent. An unknown key is an error.
_DECLARATION_SCHEMA: dict[str, dict[str, dict[str, object]]] = {
    "value": {
        "required": {"sites": _ListOf(dict)},
        "optional": {"name": str},
    },
    "site": {
        "required": {"file": str, "pattern": str},
        "optional": {"expect": str},
    },
    "anchor": {
        # `scan` is required and may not be empty. Left optional, a
        # declaration carrying only `target` and `pattern` validated, visited
        # no documents, and DOC010 reported a clean result while checking no
        # citations at all -- the same silent end state as the misspelled key
        # above, reached without a typo.
        "required": {"target": str, "pattern": str, "scan": _ListOf(str, 1)},
        "optional": {"name": str, "allow_files": _ListOf(str)},
    },
    "retired": {
        "required": {"pattern": str, "scan": _ListOf(str, 1)},
        "optional": {
            "name": str,
            "reason": str,
            "allow_files": _ListOf(str),
            "allow_after": _MappingOf(str, str),
            "strikethrough_exempt": bool,
        },
    },
}

#: The tables the declarations file itself may hold.
#:
#: `archives` and `closeout` are listed so the unknown-table guard recognizes
#: them: a table the guard has not heard of is refused, and the real
#: `config/docsync.toml` would start raising the moment one of them appeared. Their
#: keys are checked by `_validate_archives` and `_validate_closeout` rather than
#: by the generic walker, because they are values a maintenance run consumes,
#: not facts a check compares.
_TOP_LEVEL_SCHEMA: dict[str, dict[str, dict[str, object]]] = {
    "options": {"required": {}, "optional": {"strikethrough_exempt": bool}},
    "archives": {"required": {"max_lines": int, "cold_days": int}, "optional": {}},
    "closeout": {"required": {"admit_from_batch": int}, "optional": {}},
    "findings": {"required": {"grandfathered": list}, "optional": {}},
    "test_count": {"required": {}, "optional": {"pinned": int}},
    "documents": {
        "required": {},
        "optional": {
            "playbook": str,
            "findings": str,
            "agent_notes": str,
            "handoff_prompt": str,
        },
    },
}


def _where(
    kind: str, index: int, declaration: Mapping, parent: str | None = None
) -> str:
    """Name a declaration the way its author would recognise it.

    A site carries no name of its own, so it is named by its position and by
    the declaration holding it. "site 0 of value 'the responsive breakpoint'" finds
    the right four lines in the file; "value site declaration 0" does not.
    """
    name = declaration.get("name") if isinstance(declaration, Mapping) else None
    if isinstance(name, str) and name:
        base = f"{kind} {name!r}"
    else:
        base = f"{kind} {index}"
    return f"{base} of {parent}" if parent else base


def _validate(
    kind: str, index: int, declaration: object, parent: str | None = None
) -> None:
    """Check one declaration's shape, blaming the declaration rather than a doc.

    Raised as DeclarationError so the CLI reports it and exits 2. Reading a
    required key straight out of the mapping ended the run in a KeyError
    traceback and exit 1, which tells the reader nothing about which
    declaration is wrong or what is missing from it.
    """
    schema = _DECLARATION_SCHEMA[kind]
    holder = declaration if isinstance(declaration, Mapping) else {}
    where = _where(kind, index, holder, parent)
    if not isinstance(declaration, Mapping):
        raise DeclarationError(f"{where} is {type(declaration).__name__}, not a table.")

    required, optional = schema["required"], schema["optional"]
    known = {**required, **optional}
    for key in declaration:
        if key not in known:
            raise DeclarationError(
                f"{where} has an unknown key {key!r}. A misspelled key is "
                f"refused rather than ignored, because a declaration that "
                f"silently checks nothing is worse than one that fails. "
                f"Known keys: {', '.join(sorted(known))}."
            )
    for key in required:
        if key not in declaration:
            raise DeclarationError(
                f"{where} has no {key!r}, which it cannot work without."
            )
    for key, wanted in known.items():
        if key not in declaration:
            continue
        bad = _mismatch(wanted, declaration[key])
        if bad:
            raise DeclarationError(
                f"{where} gives {key!r} as {bad}. A list written as a bare "
                f"string is read one character at a time and matches nothing, "
                f"and a non-string inside one reaches the matcher as a crash."
            )

    if kind == "value":
        for site_index, site in enumerate(declaration["sites"]):
            _validate("site", site_index, site, parent=where)


def _validate_options(options: object) -> None:
    """Check the [options] table, which sets a default for every declaration.

    A typo here is the quietest fault in the file: `strikethough_exempt` reads
    as an unknown key, the real option keeps its default, and every retired
    claim the author meant to expose stays exempt.
    """
    schema = _TOP_LEVEL_SCHEMA["options"]
    if not isinstance(options, Mapping):
        raise DeclarationError(f"[options] is {type(options).__name__}, not a table.")
    for key, value in options.items():
        wanted = schema["optional"].get(key)
        if wanted is None:
            raise DeclarationError(
                f"[options] has an unknown key {key!r}. Known keys: "
                f"{', '.join(sorted(schema['optional']))}."
            )
        bad = _mismatch(wanted, value)
        if bad:
            raise DeclarationError(f"[options] gives {key!r} as {bad}.")


@dataclasses.dataclass(frozen=True)
class ArchiveConfig:
    """The thresholds a maintenance run consumes, from [archives] or defaults.

    Not a declaration: these are not facts anything compares against a
    document. They are the numbers a pagination or cold-storage run is driven
    by, which is why they are validated once here and passed in.
    """

    max_lines: int = DEFAULT_ARCHIVE_MAX_LINES
    cold_days: int = DEFAULT_ARCHIVE_COLD_DAYS


def _positive_int(table: str, key: str, value: object) -> int:
    """Return one validated positive integer from a configuration table.

    Shared by every table that carries a number, so two tables cannot disagree
    about what counts as one and the ``bool`` trap is answered in a single
    place. ``bool`` is refused before the numeric test because it subclasses
    ``int``: ``max_lines = true`` would otherwise pass as a page target of one
    line and silently repaginate the whole corpus one entry per file, and
    ``admit_from_batch = true`` would read as boundary 1, making every
    historical batch managed. Both are typos that read as success. The double
    negative is the point: a boolean is not an integer, and the message names
    the table and the key to look at.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise DeclarationError(
            f"{table} gives {key!r} as {type(value).__name__}, not an integer."
        )
    if value <= 0:
        raise DeclarationError(
            f"{table} gives {key!r} as {value}; a threshold must be positive."
        )
    return value


def _validate_archives(archives: object) -> ArchiveConfig:
    """Check a declared [archives] table and return its thresholds.

    Every key is required once the table exists, and every key is listed, for
    the same reason [options] lists its own: the quiet failure. A misspelled
    ``max_line`` would otherwise name a page size nobody chose while the gate
    stayed green.
    """
    if not isinstance(archives, Mapping):
        raise DeclarationError(f"[archives] is {type(archives).__name__}, not a table.")
    known = _TOP_LEVEL_SCHEMA["archives"]["required"]
    for key in archives:
        if key not in known:
            raise DeclarationError(
                f"[archives] has an unknown key {key!r}. Known keys: "
                f"{', '.join(sorted(known))}."
            )
    for key in known:
        if key not in archives:
            raise DeclarationError(
                f"[archives] has no {key!r}; both thresholds are required once "
                f"the table is declared."
            )
    return ArchiveConfig(
        max_lines=_positive_int("[archives]", "max_lines", archives["max_lines"]),
        cold_days=_positive_int("[archives]", "cold_days", archives["cold_days"]),
    )


def _archive_config(declarations: Mapping) -> ArchiveConfig:
    """Return the archive thresholds for an already-read declarations file.

    Absence of the table is not an error. Pagination and cold aging are opt-in
    maintenance operations, so their thresholds have a documented default and a
    repository that never paginates needs no table at all. This is the single
    place that decides that; both readers below go through it so they cannot
    disagree about what "not configured" means.
    """
    if "archives" not in declarations:
        return ArchiveConfig()
    return _validate_archives(declarations["archives"])


def load_archive_config(
    repo_root: Path, *, config_path: Path | None = None
) -> ArchiveConfig:
    """Read the repository's archive thresholds, defaults included."""
    return _archive_config(load_declarations(repo_root, config_path=config_path))


@dataclasses.dataclass(frozen=True)
class TestCountConfig:
    """The test count a human has explicitly pinned, from [test_count] or absent.

    Not a declaration: nothing else in the repository is compared against
    it, it is the fact itself. `resolved_test_count_authority`
    (`docsync.logic`) reads it in preference to re-deriving a count from
    Section 4 prose position, which is what let a same-date tie or a
    correction to an older entry (F-DOCSYNC-11, F-DOCSYNC-22) silently
    shadow the true count. Only `--fix --test-count N` writes this table
    (`cli._rewrite_test_count_pin`); nothing else may hand-edit it.
    """

    pinned: int | None = None


def _validate_test_count(table: object) -> TestCountConfig:
    """Check a declared [test_count] table and return its pin.

    The single optional key is validated the same way every other table's
    keys are: an unknown key is refused rather than ignored, and the pin
    itself is checked with the same ``_positive_int`` every other numeric
    table uses, so a typo or a quoted number cannot silently pin nothing.
    """
    if not isinstance(table, Mapping):
        raise DeclarationError(f"[test_count] is {type(table).__name__}, not a table.")
    known = _TOP_LEVEL_SCHEMA["test_count"]["optional"]
    for key in table:
        if key not in known:
            raise DeclarationError(
                f"[test_count] has an unknown key {key!r}. Known keys: "
                f"{', '.join(sorted(known))}."
            )
    if "pinned" not in table:
        return TestCountConfig()
    return TestCountConfig(
        pinned=_positive_int("[test_count]", "pinned", table["pinned"])
    )


def _test_count_config(declarations: Mapping) -> TestCountConfig:
    """Return the pinned test count for an already-read declarations file.

    Absence of the table is not an error, and returns no pin: a repository
    that has never run `--fix --test-count N` falls all the way back to
    `latest_test_count_authority`'s prose-derived cold-start answer.
    """
    if "test_count" not in declarations:
        return TestCountConfig()
    return _validate_test_count(declarations["test_count"])


def load_test_count_config(
    repo_root: Path, *, config_path: Path | None = None
) -> TestCountConfig:
    """Read the repository's pinned test count, or no pin at all."""
    return _test_count_config(load_declarations(repo_root, config_path=config_path))


@dataclasses.dataclass(frozen=True)
class CloseoutConfig:
    """Which batches a close-out check is responsible for, from [closeout].

    Not a declaration, for the same reason the archive thresholds are not: this
    decides which batch numbers the closure signals are evaluated against, it is
    not a fact compared against a document.

    One boundary rather than a recorded set of managed batches, because a set
    can be opted out of by omission and a boundary cannot: every batch at or
    above ``admit_from_batch`` is managed whether or not anything lists it. The
    boundary only moves when someone edits this file, which is a reviewable act.
    """

    admit_from_batch: int = DEFAULT_CLOSEOUT_ADMIT_FROM_BATCH


def _validate_closeout(closeout: object) -> CloseoutConfig:
    """Check a declared [closeout] table and return its admission boundary.

    The single key is required once the table exists. An empty table read as
    "nothing is managed" would silently switch off every closure signal, which
    is the same quiet failure [options] and [archives] already refuse.
    """
    if not isinstance(closeout, Mapping):
        raise DeclarationError(f"[closeout] is {type(closeout).__name__}, not a table.")
    known = _TOP_LEVEL_SCHEMA["closeout"]["required"]
    for key in closeout:
        if key not in known:
            raise DeclarationError(
                f"[closeout] has an unknown key {key!r}. Known keys: "
                f"{', '.join(sorted(known))}."
            )
    for key in known:
        if key not in closeout:
            raise DeclarationError(
                f"[closeout] has no {key!r}; the admission boundary is required "
                f"once the table is declared."
            )
    return CloseoutConfig(
        admit_from_batch=_positive_int(
            "[closeout]", "admit_from_batch", closeout["admit_from_batch"]
        )
    )


def _closeout_config(declarations: Mapping) -> CloseoutConfig:
    """Return the admission boundary for an already-read declarations file.

    Absence of the table takes the documented default rather than raising, for
    the same reason [archives] does: repositories that never wrote one still run
    the gate, and this default already admits every batch, so an absent table
    cannot be the thing that lets a closure through unchecked.
    """
    if "closeout" not in declarations:
        return CloseoutConfig()
    return _validate_closeout(declarations["closeout"])


def load_closeout_config(
    repo_root: Path, *, config_path: Path | None = None
) -> CloseoutConfig:
    """Read the repository's close-out admission boundary."""
    return _closeout_config(load_declarations(repo_root, config_path=config_path))


@dataclasses.dataclass(frozen=True)
class FindingsConfig:
    """Which findings predate the lifecycle rule, from [findings].

    A list of ids rather than a boundary, which is the opposite of
    ``CloseoutConfig`` and deliberately so. A boundary works when what it
    admits is ordered: every batch at or above a number. Finding ids are not
    ordered -- a source tag like ``F-DOCSYNC-9`` carries no batch to compare
    -- so any boundary drawn over batch numbers leaves every tagged id on one
    side of it by accident, and a new finding could pick a tag and escape.

    An explicit list cannot be escaped by naming: anything absent is admitted.
    It only ever shrinks, and both directions are a reviewable diff, so the
    backlog cannot be quietly forgiven one id at a time.

    The default is empty -- strict. A repository that declares nothing admits
    every finding, so this mechanism carries no repository's history in it.
    """

    grandfathered: tuple[str, ...] = ()


def _validate_findings(findings: object) -> FindingsConfig:
    """Check a declared [findings] table and return its grandfathered ids."""
    if not isinstance(findings, Mapping):
        raise DeclarationError(f"[findings] is {type(findings).__name__}, not a table.")
    known = _TOP_LEVEL_SCHEMA["findings"]["required"]
    for key in findings:
        if key not in known:
            raise DeclarationError(
                f"[findings] has an unknown key {key!r}. Known keys: "
                f"{', '.join(sorted(known))}."
            )
    for key in known:
        if key not in findings:
            raise DeclarationError(
                f"[findings] has no {key!r}; the grandfathered list is required "
                f"once the table is declared. Write an empty list to admit "
                f"every finding."
            )
    raw = findings["grandfathered"]
    if not isinstance(raw, list):
        raise DeclarationError(
            f"[findings] grandfathered is {type(raw).__name__}, not a list."
        )
    for entry in raw:
        if not isinstance(entry, str) or not entry.strip():
            raise DeclarationError(
                f"[findings] grandfathered holds {entry!r}; every entry must be "
                f"a finding id such as 'F-B21-1'."
            )
    return FindingsConfig(grandfathered=tuple(raw))


def _findings_config(declarations: Mapping) -> FindingsConfig:
    """Return the grandfathered ids for an already-read declarations file."""
    if "findings" not in declarations:
        return FindingsConfig()
    return _validate_findings(declarations["findings"])


def load_findings_config(
    repo_root: Path, *, config_path: Path | None = None
) -> FindingsConfig:
    """Read the repository's grandfathered finding ids."""
    return _findings_config(load_declarations(repo_root, config_path=config_path))


@dataclasses.dataclass(frozen=True)
class DocumentsConfig:
    """Where docsync's own live documents live, from [documents] or defaults.

    The defaults are docsync's generic vocabulary -- true for any repository that adopts
    the tool unmodified (docs/agents/AGENT_NOTES.md "This repository is also a template
    being extracted"). This repository overrides every field in its own declarations
    file, since the four documents moved under docs/agents/.
    """

    playbook: str = "PLAYBOOK.md"
    findings: str = "FINDINGS.md"
    agent_notes: str = "AGENT_NOTES.md"
    handoff_prompt: str = "HANDOFF_PROMPT.md"


def _validate_documents(documents: object, repo_root: Path) -> DocumentsConfig:
    """Check that each document role names one distinct in-repository path."""
    if not isinstance(documents, Mapping):
        raise DeclarationError(
            f"[documents] is {type(documents).__name__}, not a table."
        )
    schema = _TOP_LEVEL_SCHEMA["documents"]["optional"]
    kwargs: dict[str, str] = {}
    for key, value in documents.items():
        if key not in schema:
            raise DeclarationError(
                f"[documents] has an unknown key {key!r}. Known keys: "
                f"{', '.join(sorted(schema))}."
            )
        if not isinstance(value, str) or not value:
            raise DeclarationError(
                f"[documents] gives {key!r} as {type(value).__name__}, not a string."
            )
        kwargs[key] = value
    result = DocumentsConfig(**kwargs)
    seen: dict[str, str] = {}
    for role, value in (
        ("agents", "AGENTS.md"),
        ("handoff_prompt", result.handoff_prompt),
        ("agent_notes", result.agent_notes),
        ("playbook", result.playbook),
        ("findings", result.findings),
    ):
        if Path(value).is_absolute() or PureWindowsPath(value).anchor or "\\" in value:
            raise DeclarationError(
                f"[documents] {role!r} must be a repository-relative path: {value!r}."
            )
        try:
            path = resolve_within(repo_root, value)
        except SyncError as exc:
            raise DeclarationError(
                f"[documents] {role!r} must be a repository-relative path: {value!r}."
            ) from exc
        if path.is_dir():
            raise DeclarationError(
                f"[documents] {role!r} names a directory, not a document: {value!r}."
            )
        key = path.as_posix().casefold()
        if key in seen:
            raise DeclarationError(
                f"[documents] {role!r} and {seen[key]!r} resolve to the same path: {value!r}."
            )
        seen[key] = role
    return result


def _documents_config(declarations: Mapping, repo_root: Path) -> DocumentsConfig:
    """Return the document paths for an already-read declarations file."""
    if "documents" not in declarations:
        return DocumentsConfig()
    return _validate_documents(declarations["documents"], repo_root)


def load_documents_config(
    repo_root: Path, *, config_path: Path | None = None
) -> DocumentsConfig:
    """Read the repository's document paths, defaults included."""
    return _documents_config(
        load_declarations(repo_root, config_path=config_path), repo_root
    )


def _issue(
    code: str, path: str, line: int | None, invariant: str, remediation: str
) -> IntegrityIssue:
    """Build one diagnostic in the shape the integrity gate already renders."""
    return IntegrityIssue(
        code=code,
        severity="error",
        path=path,
        line=line,
        invariant=invariant,
        remediation=remediation,
    )


def load_declarations(repo_root: Path, *, config_path: Path | None = None) -> dict:
    """Read the declarations file, or return nothing if there is none.

    A repository with no declarations file at the default path is not an error.
    An explicit ``config_path`` that does not exist is: a mistyped --config
    would otherwise run every check with nothing declared, and pass.
    """
    path = config_path if config_path is not None else repo_root / DECLARATIONS_FILENAME
    if config_path is not None:
        try:
            path = resolve_within(repo_root, path)
        except SyncError as exc:
            raise DeclarationError(
                f"--config path {config_path} must be inside the repository."
            ) from exc
    if not path.is_file():
        if config_path is not None:
            raise DeclarationError(f"--config names {path}, which is not a file.")
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise DeclarationError(f"{path} is not valid TOML: {exc}") from exc


class _Files:
    """Reads repository files once, preferring the in-memory copy.

    The gate runs over documents it may have just rewritten in memory, so a
    check that went to disk would grade the previous version. Anything not
    held in memory -- a stylesheet, a script -- is read from disk and cached,
    because several declarations tend to name the same file.
    """

    def __init__(self, repo_root: Path, live: Mapping[str, list[str]]):
        self._root = repo_root.resolve()
        self._live = live
        self._cache: dict[str, list[str] | None] = {}

    def _path(self, rel_path: str) -> Path:
        """Resolve one declaration path and keep it inside the repository."""
        candidate = (self._root / rel_path).resolve()
        try:
            candidate.relative_to(self._root)
        except ValueError:
            raise DeclarationError(
                f"{DECLARATIONS_FILENAME} path {rel_path!r} resolves outside "
                "the repository root"
            ) from None
        return candidate

    def _relative(self, path: Path, declared: str) -> str:
        """Return a matched path relative to the root, rejecting symlink escape."""
        candidate = path.resolve()
        try:
            return candidate.relative_to(self._root).as_posix()
        except ValueError:
            raise DeclarationError(
                f"{DECLARATIONS_FILENAME} path {declared!r} resolves outside "
                "the repository root"
            ) from None

    def lines(self, rel_path: str) -> list[str] | None:
        """Return the file's lines, or None when it does not exist."""
        path = self._path(rel_path)
        key = self._relative(path, rel_path)
        if key in self._live:
            return list(self._live[key])
        if key not in self._cache:
            try:
                self._cache[key] = path.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
            except OSError:
                self._cache[key] = None
        cached = self._cache[key]
        return list(cached) if cached is not None else None


def _compile(pattern: str, where: str) -> re.Pattern[str]:
    """Compile a declared pattern, blaming the declaration when it is bad."""
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise DeclarationError(
            f"{where}: {pattern!r} is not a valid regex: {exc}"
        ) from exc


def _compile_value(pattern: str, expect: str | None, where: str) -> re.Pattern[str]:
    """Compile a value pattern and validate its single-value capture."""
    compiled = _compile(pattern, where)
    if compiled.groups > 1:
        raise DeclarationError(
            f"{where}: a value pattern may capture at most one value; "
            f"it has {compiled.groups} capture groups"
        )
    if expect is not None and compiled.groups == 0:
        raise DeclarationError(
            f"{where} declares expect={expect!r}, but its pattern captures "
            f"nothing to compare"
        )
    return compiled


def _compile_anchor(pattern: str, where: str) -> re.Pattern[str]:
    """Compile an anchor pattern and validate its positional captures."""
    compiled = _compile(pattern, where)
    if compiled.groups not in {1, 2}:
        raise DeclarationError(
            f"{where}: the pattern must capture one heading and may capture "
            f"one numeric item; it has {compiled.groups} capture group(s)"
        )
    return compiled


def _missing_file_issue(code: str, rel_path: str, name: str) -> IntegrityIssue:
    """One shape for "the declaration names a file that is not there"."""
    return _issue(
        code,
        DECLARATIONS_FILENAME,
        None,
        f"The declaration {name!r} names {rel_path}, which does not exist.",
        f"Point the declaration at the file that holds this fact now, or "
        f"delete the declaration if {rel_path} is gone for good.",
    )


# ----------------------------------------------------------------------
# DOC009 -- a value written in several places agrees with itself
# ----------------------------------------------------------------------


def check_values(files: _Files, declarations: Iterable[dict]) -> list[IntegrityIssue]:
    """Every site of a shared value still states it, and states the same one.

    A declared pattern behaves in one of two ways, and which one is decided by
    the pattern itself rather than by another field:

    - **With a capture group**, the captured text is compared across sites.
      Use this where the value is genuinely the same string in each place, as
      a version pin or a count is.
    - **With no capture group**, the pattern only has to match. Use this where
      the sites express one fact in different notations. The breakpoint is the
      real example: a stylesheet's exclusive maximum stops just short of the
      inclusive threshold used by a script. Comparing those two strings would
      fail on correct code, so each site declares the literal it must contain.
    """
    issues: list[IntegrityIssue] = []
    for index, declaration in enumerate(declarations):
        _validate("value", index, declaration)
        name = declaration.get("name", "<unnamed>")
        sites = declaration.get("sites", [])
        if len(sites) < 2:
            raise DeclarationError(
                f"value {name!r} declares {len(sites)} site(s); "
                f"a value written in one place cannot disagree with itself"
            )

        captured: list[tuple[str, str]] = []
        first_line: dict[str, int] = {}
        declared_expects = {
            site["expect"] for site in sites if site.get("expect") is not None
        }
        uniform_expect = (
            next(iter(declared_expects)) if len(declared_expects) == 1 else None
        )
        for site in sites:
            rel_path = site["file"]
            expect = site.get("expect")
            pattern = _compile_value(
                site["pattern"], expect, f"value {name!r} for {rel_path}"
            )
            lines = files.lines(rel_path)
            if lines is None:
                issues.append(_missing_file_issue("DOC009", rel_path, name))
                continue

            # Every occurrence, not the first. Stopping at the first match
            # accepted a file that stated the value once and contradicted it
            # further down: index.css carries the breakpoint in three media
            # queries, and only one of them was ever read.
            #
            # The shared matcher adds cross-line matches without replacing the
            # raw per-line scan. A media query or sentence that wraps would be
            # invisible to the line scan alone; replacing it made ^, $ and
            # indentation mean something new. Here the miss is quiet when an
            # unwrapped copy satisfies the check while a drifted wrapped one
            # goes unread, which is the exact hole "every occurrence" closes.
            found: list[tuple[int, str | None]] = [
                (
                    line_number,
                    match.group(1) if match.groups() else None,
                )
                for match, line_number, _text, _position in _declared_matches(
                    pattern, lines
                )
            ]

            if not found:
                issues.append(
                    _issue(
                        "DOC009",
                        rel_path,
                        None,
                        f"{rel_path} no longer states {name!r}.",
                        f"This file is one of {len(sites)} that must agree on "
                        f"{name!r}. Either restore the value here, or change "
                        f"every site and the declaration together.",
                    )
                )
                continue

            if pattern.groups:
                missing_capture = next(
                    ((line, value) for line, value in found if value is None), None
                )
                if missing_capture is not None:
                    raise DeclarationError(
                        f"value {name!r} for {rel_path}: the value capture "
                        f"matched nothing at line {missing_capture[0]}"
                    )
                empty_capture = next(
                    ((line, value) for line, value in found if value == ""), None
                )
                if empty_capture is not None:
                    raise DeclarationError(
                        f"value {name!r} for {rel_path}: the pattern captured "
                        f"an empty value at line {empty_capture[0]}"
                    )

            first_line[rel_path] = found[0][0]
            values = [value for _line, value in found if value is not None]
            if expect is not None and not values:
                raise DeclarationError(
                    f"value {name!r} declares expect={expect!r} for {rel_path}, "
                    f"but its pattern captures nothing to compare"
                )

            # A declared expectation is checked against every occurrence, so a
            # file is held to one reading of the fact throughout.
            if expect is not None:
                wrong = [(line, value) for line, value in found if value != expect]
                if wrong:
                    issues.append(
                        _issue(
                            "DOC009",
                            rel_path,
                            wrong[0][0],
                            f"{rel_path} states {name!r} as {wrong[0][1]} here "
                            f"and the declaration expects {expect}.",
                            "Every occurrence in this file must read the same. "
                            "Change it, or change the declaration if the value "
                            "itself has moved.",
                        )
                    )
                elif uniform_expect is not None:
                    captured.append((rel_path, expect))
                continue

            if values:
                distinct_here = sorted(set(values))
                if len(distinct_here) > 1:
                    issues.append(
                        _issue(
                            "DOC009",
                            rel_path,
                            found[0][0],
                            f"{rel_path} contradicts itself on {name!r}: "
                            f"{', '.join(distinct_here)}.",
                            "One file, one reading of the fact. Decide which "
                            "is right before comparing it with the other "
                            "sites.",
                        )
                    )
                    continue
                captured.append((rel_path, distinct_here[0]))

        if len(captured) > 1:
            distinct = {value for _path, value in captured}
            if len(distinct) > 1:
                reported = ", ".join(f"{path} says {value}" for path, value in captured)
                first_path = captured[0][0]
                issues.append(
                    _issue(
                        "DOC009",
                        first_path,
                        first_line.get(first_path),
                        f"The sites for {name!r} disagree: {reported}.",
                        "Decide which value is right, change every site to it, "
                        "and say in the commit which sites you checked.",
                    )
                )
    return issues


# ----------------------------------------------------------------------
# DOC010 -- a cross-reference resolves to something that exists
# ----------------------------------------------------------------------


def _headings(lines: list[str]) -> dict[str, int]:
    """Map every citable place in the document to the line it sits on.

    Both spellings count. A hash heading is the obvious one; a bold lead-in is
    how docs/design/README.md marks its sections, and citing one of those is
    citing a real place. Each is also indexed without a trailing parenthetical,
    so a citation of "Session Bootstrap" resolves to the heading actually
    written as "Session Bootstrap (in order)".
    """
    found: dict[str, int] = {}
    for source_index, line in prose_lines(lines):
        index = source_index + 1
        match = _HEADING_RE.match(line) or _BOLD_LABEL_RE.match(line)
        if not match:
            continue
        text = match.group(1).strip()
        for form in (
            text,
            _HEADING_SUFFIX_RE.sub("", text),
            _LABEL_TAIL_RE.sub("", text).rstrip(" .-—"),
        ):
            if form:
                found.setdefault(form, index)
    return found


def _list_numbers_under(lines: list[str], heading_line: int) -> set[int]:
    """Return the ordered-list numbers between this heading and the next.

    Scoped to the section, because a document has many numbered lists and a
    citation of "item 6" means the sixth item of that section's list, not the
    sixth anywhere in the file.
    """
    numbers: set[int] = set()
    for index, line in prose_lines(lines):
        if index < heading_line:
            continue
        if _HEADING_RE.match(line):
            break
        item = _LIST_ITEM_RE.match(line)
        if item:
            numbers.add(int(item.group(1)))
    return numbers


def check_anchors(files: _Files, declarations: Iterable[dict]) -> list[IntegrityIssue]:
    """Every citation of a declared shape resolves in the document it names.

    The declaration describes a *shape* of citation rather than one citation,
    so a reference written tomorrow is checked without anyone declaring it.
    That matters: the citation this check exists for was written and broken on
    the same day, and nobody would have declared it in between.
    """
    issues: list[IntegrityIssue] = []
    for index, declaration in enumerate(declarations):
        _validate("anchor", index, declaration)
        name = declaration.get("name", "<unnamed>")
        pattern = _compile_anchor(declaration["pattern"], f"anchor {name!r}")
        target_path = declaration["target"]
        target_lines = files.lines(target_path)
        if target_lines is None:
            issues.append(_missing_file_issue("DOC010", target_path, name))
            continue

        headings = _headings(target_lines)
        allow_files = declaration.get("allow_files", [])

        for rel_path in _effective_scan(
            files, declaration.get("scan", []), allow_files, f"anchor {name!r}"
        ):
            lines = files.lines(rel_path)
            if lines is None:
                issues.append(_missing_file_issue("DOC010", rel_path, name))
                continue
            # The shared matcher adds citations that cross a line boundary and
            # keeps raw-line matches for their original regex semantics.
            # Wrapping is the one edit a document gets for free -- PLAYBOOK.md
            # already carried `AGENTS.md` "UI and / Accessibility Rules"
            # across two lines, so a per-line-only gate could not have caught
            # that heading moving.
            for match, line_number, _text, _position in _declared_matches(
                pattern, _prose_source(lines)
            ):
                heading = match.group(1)
                item = match.group(2) if len(match.groups()) > 1 else None
                if not heading:
                    raise DeclarationError(
                        f"anchor {name!r}: the required heading capture matched "
                        f"nothing in {rel_path}:{line_number}"
                    )
                if item is not None and re.fullmatch(r"[0-9]+", item) is None:
                    raise DeclarationError(
                        f"anchor {name!r}: the optional numeric item capture "
                        f"matched {item!r} in {rel_path}:{line_number}"
                    )
                if heading not in headings:
                    issues.append(
                        _issue(
                            "DOC010",
                            rel_path,
                            line_number,
                            f'{rel_path} cites "{heading}" in '
                            f"{target_path}, which has no such heading.",
                            "Find where that rule lives now and cite it "
                            "by its current heading. Moving a rule and "
                            "leaving the pointer behind is the defect "
                            "this check exists for.",
                        )
                    )
                    continue
                if item is None:
                    continue
                available = _list_numbers_under(target_lines, headings[heading])
                if int(item) not in available:
                    issues.append(
                        _issue(
                            "DOC010",
                            rel_path,
                            line_number,
                            f'{rel_path} cites item {item} of "{heading}" '
                            f"in {target_path}, which has "
                            f"{len(available)} item(s).",
                            "Renumbering a list breaks every citation of "
                            "it. Cite the item that holds the rule now.",
                        )
                    )
    return issues


# ----------------------------------------------------------------------
# DOC011 -- a retired claim does not survive where it still prescribes
# ----------------------------------------------------------------------


def check_retired(
    files: _Files,
    declarations: Iterable[dict],
    *,
    strikethrough_exempt: bool = DEFAULT_STRIKETHROUGH_EXEMPT,
) -> list[IntegrityIssue]:
    """A claim that is no longer true is gone from every document that acts.

    History is exempt on purpose. A dated log entry recording what a decision
    said on the day it was made is correct and stays; `AGENTS.md` already
    treats a point-in-time record as accurate at write time. What must not
    survive is a copy that still tells the next agent what to do.

    ``allow_files`` exempts whole files by glob. ``allow_after`` exempts the
    part of one file below a marker line, which is how an execution log inside
    a live document is exempted without exempting the document.

    ``strikethrough_exempt`` is the third exemption and the only one that is a
    guess about what an author meant. It is declared rather than assumed, per
    declaration or once under ``[options]``, because a repository that uses
    strikethrough rhetorically would otherwise get a silent blind spot.
    """
    issues: list[IntegrityIssue] = []
    for index, declaration in enumerate(declarations):
        _validate("retired", index, declaration)
        name = declaration.get("name", "<unnamed>")
        reason = declaration.get("reason", "")
        pattern = _compile(declaration["pattern"], f"retired {name!r}")
        allow_files = declaration.get("allow_files", [])
        allow_after = declaration.get("allow_after", {})
        skip_struck = declaration.get("strikethrough_exempt", strikethrough_exempt)

        for rel_path in _effective_scan(
            files, declaration.get("scan", []), allow_files, f"retired {name!r}"
        ):
            lines = files.lines(rel_path)
            if lines is None:
                issues.append(_missing_file_issue("DOC011", rel_path, name))
                continue

            exempt_from = None
            marker = allow_after.get(rel_path)
            if marker:
                candidates = dict(marker_lines(lines))
                for index, line in enumerate(lines, start=1):
                    if line.strip() == marker.strip() and index - 1 in candidates:
                        exempt_from = index
                        break

            # Cross-line matches supplement, rather than replace, raw-line
            # matches. A phrase that wraps -- `limit_results` ending one line
            # and "inside the thresholds disclosure" starting the next -- can
            # never match a per-line search, while replacing that search loses
            # line anchors. Newlines become spaces only for the cross-line pass.
            for _match, line_number, text, position in _declared_matches(
                pattern, _prose_source(lines)
            ):
                if exempt_from is not None and line_number >= exempt_from:
                    continue
                if skip_struck and fully_struck(
                    text, position, position + len(_match.group(0))
                ):
                    continue
                issues.append(
                    _issue(
                        "DOC011",
                        rel_path,
                        line_number,
                        f"{rel_path} still states {name!r}, which was "
                        f"retired. {reason}".strip(),
                        "Update this copy. A reversal recorded in one "
                        "place while the normative copies still prescribe "
                        "the old behaviour is how an agent undoes it.",
                    )
                )
    return issues


def _prose_source(lines: list[str]) -> list[str]:
    """Keep line coordinates while excluding example/comment content."""
    visible = dict(prose_lines(lines))
    return [visible.get(index, "") for index in range(len(lines))]


def _joined_text(lines: list[str]) -> tuple[str, list[int]]:
    """Return the document as one string, plus each line's start offset.

    Each line is stripped before joining, and the lines are joined with a
    single space, so a wrapped phrase reads the way it would be spoken. The
    stripping is what makes the join useful rather than merely different: a
    continuation line carries the indentation of whatever list or block it
    sits in, and joining raw lines puts that indentation *inside* the phrase.
    A citation wrapped as `"UI and` / `    Accessibility Rules"` then joins to
    five spaces in the middle of the heading and still matches nothing.

    Indentation is presentation, not content, so dropping it costs nothing and
    an offset built from the stripped pieces still maps a match back to the
    line a reader has to open.

    This handles a wrap. It does not handle arbitrary reflow: a pattern
    written with a literal single space still needs the two words it joins to
    end up one space apart, which they do here and would not if a document
    put two spaces between sentences mid-phrase.
    """
    pieces: list[str] = []
    starts: list[int] = []
    position = 0
    for line in lines:
        piece = line.strip()
        starts.append(position)
        position += len(piece) + 1
        pieces.append(piece)
    return " ".join(pieces), starts


def _declared_matches(
    pattern: re.Pattern[str], lines: list[str]
) -> list[tuple[re.Match[str], int, str, int]]:
    """Find original per-line matches plus matches that cross a line boundary.

    The raw line remains authoritative for a match contained on one line, so
    ``^``, ``$`` and indentation keep their original meaning. The joined form
    contributes only matches that reach text on a later line. Each result
    retains its source text and local offset for the strikethrough exemption.
    """
    joined, starts = _joined_text(lines)
    found: list[tuple[int, int, re.Match[str], int, str, int]] = []

    for match in pattern.finditer(joined):
        line_number = _line_of(starts, match.start())
        if line_number >= len(starts) or match.end() <= starts[line_number]:
            continue
        found.append(
            (
                match.start(),
                match.end(),
                match,
                line_number,
                joined,
                match.start(),
            )
        )

    for line_number, line in enumerate(lines, start=1):
        line_start = starts[line_number - 1]
        leading_space = len(line) - len(line.lstrip())
        for match in pattern.finditer(line):
            absolute_start = line_start + max(match.start() - leading_space, 0)
            absolute_end = absolute_start + len(match.group(0))
            found.append(
                (
                    absolute_start,
                    absolute_end,
                    match,
                    line_number,
                    line,
                    match.start(),
                )
            )

    found.sort(key=lambda item: (item[0], item[1]))
    return [
        (match, line_number, text, position)
        for _start, _end, match, line_number, text, position in found
    ]


def _line_of(starts: list[int], position: int) -> int:
    """Return the 1-based line holding this offset in the joined text."""
    low, high = 0, len(starts) - 1
    while low < high:
        middle = (low + high + 1) // 2
        if starts[middle] <= position:
            low = middle
        else:
            high = middle - 1
    return low + 1


# ----------------------------------------------------------------------
# Shared
#
# _joined_text and _line_of sit above rather than here only because DOC011
# needed them first. All three checks read from them now.
# ----------------------------------------------------------------------


def _is_struck_through(line: str, position: int) -> bool:
    """Is the match inside ~~...~~ on this line?

    A plan step that has been superseded is often kept, struck through, with
    the reversal written above it. That is a record of what was decided, not
    an instruction, and it is the one form of retired claim worth keeping in
    place -- deleting it would lose why the step existed at all.
    """
    return fully_struck(line, position, position + 1)


def _expand(files: _Files, patterns: Iterable[str]) -> list[str]:
    """Turn declared scan globs into repository-relative paths.

    Globs are matched against the filesystem rather than the tracked set. An
    unmatched glob stays in the result so the caller reports it like a named
    file that disappeared; dropping it would silently narrow the declaration.
    """
    found: list[str] = []
    for pattern in patterns:
        files._path(pattern)
        if any(ch in pattern for ch in "*?["):
            matched = False
            for path in sorted(files._root.glob(pattern)):
                if path.is_file():
                    matched = True
                    found.append(files._relative(path, pattern))
            if not matched:
                found.append(pattern)
        else:
            found.append(pattern)
    # Stable and unique: a file named by two globs is checked once.
    return sorted(dict.fromkeys(found))


def _effective_scan(
    files: _Files,
    patterns: Iterable[str],
    allow_files: Iterable[str],
    where: str,
) -> list[str]:
    """Expand a scan and refuse an allow list that excludes all of it."""
    expanded = _expand(files, patterns)
    included = [
        rel_path
        for rel_path in expanded
        if not any(fnmatch.fnmatch(rel_path, glob) for glob in allow_files)
    ]
    if not included:
        raise DeclarationError(
            f"{where}: allow_files exempts every scan path, so the declaration "
            f"would inspect no documents"
        )
    return included


def collect_declaration_issues(
    *,
    repo_root: Path,
    live_documents: Mapping[str, list[str]],
    config_path: Path | None = None,
) -> list[IntegrityIssue]:
    """Run every declared check and return the diagnostics in a stable order."""
    declarations = load_declarations(repo_root, config_path=config_path)
    if not declarations:
        return []

    # The table names too. A misspelled [[ancor]] parses as valid TOML, is
    # never read, and leaves the gate green with one fewer check running.
    known_tables = set(_DECLARATION_SCHEMA) | set(_TOP_LEVEL_SCHEMA)
    known_tables.discard("site")
    # Under --config the file actually read is config_path, not the
    # repository default: naming DECLARATIONS_FILENAME here would point the
    # reader at a file this run never opened.
    source = config_path if config_path is not None else DECLARATIONS_FILENAME
    for table in declarations:
        if table not in known_tables:
            raise DeclarationError(
                f"{source} has an unknown table {table!r}. "
                f"Known tables: {', '.join(sorted(known_tables))}."
            )
    _validate_options(declarations.get("options", {}))
    # Validated here as well as at the maintenance entry point, so a bad table
    # is refused by every command that reads the file and not only by the one
    # that happens to consume the thresholds.
    _archive_config(declarations)
    _closeout_config(declarations)
    _documents_config(declarations, repo_root)

    # Validate the outer collections before a collector tries to iterate one.
    # Per-declaration validation starts inside that iteration, so it cannot
    # turn ``anchor = 1`` into the input error the CLI knows how to report.
    collections: dict[str, list] = {}
    for kind in ("value", "anchor", "retired"):
        collection = declarations.get(kind, [])
        if not isinstance(collection, list):
            raise DeclarationError(
                f"top-level {kind!r} is {type(collection).__name__}, not a "
                f"list of tables. Write each declaration as [[{kind}]]."
            )
        collections[kind] = collection

    files = _Files(repo_root, live_documents)
    issues: list[IntegrityIssue] = []
    issues.extend(check_values(files, collections["value"]))
    issues.extend(check_anchors(files, collections["anchor"]))
    options = declarations.get("options", {})
    issues.extend(
        check_retired(
            files,
            collections["retired"],
            strikethrough_exempt=options.get(
                "strikethrough_exempt", DEFAULT_STRIKETHROUGH_EXEMPT
            ),
        )
    )
    return sorted(issues, key=lambda issue: (issue.path, issue.line or 0, issue.code))
