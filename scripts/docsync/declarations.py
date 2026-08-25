"""Deterministic checks for facts that are written down more than once.

Six of the nineteen review comments Batch 21 drew were not logic defects. They
were one fact recorded in several places, where the copies had drifted: a
breakpoint that read 860 in a stylesheet and 768 in a script, a reversed
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

import fnmatch
import re
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path

from docsync.models import IntegrityIssue, SyncError

#: Where the repository's own declarations live, relative to the repo root.
DECLARATIONS_FILENAME = ".docsync.toml"

#: A heading in a Markdown document: one to six hashes, then the text.
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")

#: An ordered-list item at the start of a line: "3. **Something**".
_LIST_ITEM_RE = re.compile(r"^(\d+)\.\s")

#: A bold lead-in used as a section marker: "**Wordmark animation** ...".
#: docs/design/README.md labels its sections this way rather than with
#: hashes, and a citation of one is a citation of a real place in the file.
#:
#: The list bullet is optional because that document labels sections both
#: ways. "- **Responsive.** Single breakpoint at 860px." is a section of it,
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
_STRIKETHROUGH_RE = re.compile(r"~~.+?~~")

#: What `strikethrough_exempt` defaults to when nothing declares it. On,
#: because it matches the convention most Markdown corpora follow -- but the
#: option exists so a corpus that does not follow it can say so.
DEFAULT_STRIKETHROUGH_EXEMPT = True


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


#: What a declaration of each kind may hold, and what type each key takes.
#:
#: Every key is listed rather than only the required ones, because the worst
#: way a declarations file can be wrong is quietly. A misspelled `scans` left
#: the declaration scanning nothing and the gate green, which is the exact
#: failure this whole module exists to prevent. An unknown key is an error.
_DECLARATION_SCHEMA: dict[str, dict[str, dict[str, type]]] = {
    "value": {
        "required": {"sites": list},
        "optional": {"name": str},
    },
    "site": {
        "required": {"file": str, "pattern": str},
        "optional": {"expect": str},
    },
    "anchor": {
        "required": {"target": str, "pattern": str},
        "optional": {"name": str, "scan": list, "allow_files": list},
    },
    "retired": {
        "required": {"pattern": str},
        "optional": {
            "name": str,
            "reason": str,
            "scan": list,
            "allow_files": list,
            "allow_after": dict,
            "strikethrough_exempt": bool,
        },
    },
}

#: The tables the declarations file itself may hold.
_TOP_LEVEL_SCHEMA = {
    "options": {"required": {}, "optional": {"strikethrough_exempt": bool}},
}


def _where(
    kind: str, index: int, declaration: Mapping, parent: str | None = None
) -> str:
    """Name a declaration the way its author would recognise it.

    A site carries no name of its own, so it is named by its position and by
    the declaration holding it. "site 0 of value 'the 860px breakpoint'" finds
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
        if key in declaration and not isinstance(declaration[key], wanted):
            raise DeclarationError(
                f"{where} gives {key!r} as {type(declaration[key]).__name__}, "
                f"not {wanted.__name__}. A list written as a bare string is "
                f"read one character at a time and matches nothing."
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
        if not isinstance(value, wanted):
            raise DeclarationError(
                f"[options] gives {key!r} as {type(value).__name__}, "
                f"not {wanted.__name__}."
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


def load_declarations(repo_root: Path) -> dict:
    """Read the declarations file, or return nothing if there is none.

    A repository with no declarations is not an error. That is the state every
    repository starts in, and the checks simply have nothing to say.
    """
    path = repo_root / DECLARATIONS_FILENAME
    if not path.is_file():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise DeclarationError(f"{DECLARATIONS_FILENAME} is not valid TOML: {exc}")


class _Files:
    """Reads repository files once, preferring the in-memory copy.

    The gate runs over documents it may have just rewritten in memory, so a
    check that went to disk would grade the previous version. Anything not
    held in memory -- a stylesheet, a script -- is read from disk and cached,
    because several declarations tend to name the same file.
    """

    def __init__(self, repo_root: Path, live: Mapping[str, list[str]]):
        self._root = repo_root
        self._live = live
        self._cache: dict[str, list[str] | None] = {}

    def lines(self, rel_path: str) -> list[str] | None:
        """Return the file's lines, or None when it does not exist."""
        if rel_path in self._live:
            return list(self._live[rel_path])
        if rel_path not in self._cache:
            path = self._root / rel_path
            try:
                self._cache[rel_path] = path.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
            except OSError:
                self._cache[rel_path] = None
        cached = self._cache[rel_path]
        return list(cached) if cached is not None else None


def _compile(pattern: str, where: str) -> re.Pattern[str]:
    """Compile a declared pattern, blaming the declaration when it is bad."""
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise DeclarationError(f"{where}: {pattern!r} is not a valid regex: {exc}")


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
      real example: a stylesheet writes ``859.98px`` because a media query
      stops just short, and a script writes ``860``. Comparing those two
      strings would fail on correct code, so each site declares the literal it
      must still contain.
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
        for site in sites:
            rel_path = site["file"]
            lines = files.lines(rel_path)
            if lines is None:
                issues.append(_missing_file_issue("DOC009", rel_path, name))
                continue

            pattern = _compile(site["pattern"], f"value {name!r}")
            expect = site.get("expect")

            # Every occurrence, not the first. Stopping at the first match
            # accepted a file that stated the value once and contradicted it
            # further down: index.css carries the breakpoint in three media
            # queries, and only one of them was ever read.
            #
            # Read from the joined document for the same reason DOC010 and
            # DOC011 are: a media query or a sentence that wraps is invisible
            # to a per-line search. Here the miss is quiet rather than loud
            # only when a file states the value more than once -- the
            # unwrapped copy satisfies the check while a drifted wrapped one
            # goes unread, which is the exact hole "every occurrence" was
            # meant to close.
            joined, starts = _joined_text(lines)
            found: list[tuple[int, str | None]] = [
                (
                    _line_of(starts, match.start()),
                    match.group(1) if match.groups() else None,
                )
                for match in pattern.finditer(joined)
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
    for index, line in enumerate(lines, start=1):
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
    for line in lines[heading_line:]:
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
        target_path = declaration["target"]
        target_lines = files.lines(target_path)
        if target_lines is None:
            issues.append(_missing_file_issue("DOC010", target_path, name))
            continue

        headings = _headings(target_lines)
        pattern = _compile(declaration["pattern"], f"anchor {name!r}")
        allow_files = declaration.get("allow_files", [])

        for rel_path in _expand(files, declaration.get("scan", [])):
            if any(fnmatch.fnmatch(rel_path, glob) for glob in allow_files):
                continue
            lines = files.lines(rel_path)
            if lines is None:
                continue
            # Matched against the joined document, as DOC011 already is. A
            # citation that wraps is invisible to a per-line search, and
            # wrapping is the one edit a document gets for free -- PLAYBOOK.md
            # already carried `AGENTS.md` "UI and / Accessibility Rules"
            # across two lines, so the gate could not have caught that heading
            # moving.
            joined, starts = _joined_text(lines)
            for match in pattern.finditer(joined):
                line_number = _line_of(starts, match.start())
                heading = match.group(1)
                item = match.group(2) if len(match.groups()) > 1 else None
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

        for rel_path in _expand(files, declaration.get("scan", [])):
            if any(fnmatch.fnmatch(rel_path, glob) for glob in allow_files):
                continue
            lines = files.lines(rel_path)
            if lines is None:
                continue

            exempt_from = None
            marker = allow_after.get(rel_path)
            if marker:
                for index, line in enumerate(lines, start=1):
                    if marker in line:
                        exempt_from = index
                        break

            # Matched against the whole document, not line by line. A phrase
            # that wraps -- `limit_results` ending one line and "inside the
            # thresholds disclosure" starting the next -- can never match a
            # per-line search, and wrapping is the one edit a document gets
            # for free. Newlines become spaces so a pattern written for prose
            # still reads as prose.
            joined, starts = _joined_text(lines)
            for match in pattern.finditer(joined):
                line_number = _line_of(starts, match.start())
                if exempt_from is not None and line_number >= exempt_from:
                    continue
                if skip_struck and _is_struck_through(joined, match.start()):
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
    return any(
        span.start() <= position < span.end()
        for span in _STRIKETHROUGH_RE.finditer(line)
    )


def _expand(files: _Files, patterns: Iterable[str]) -> list[str]:
    """Turn declared scan globs into repository-relative paths.

    Globs are matched against the filesystem rather than the tracked set,
    because a declaration that stops matching when a file is renamed should
    report nothing rather than silently narrow its scope. The missing-file
    diagnostics above cover the named-file case.
    """
    found: list[str] = []
    for pattern in patterns:
        if any(ch in pattern for ch in "*?["):
            for path in sorted(files._root.glob(pattern)):
                if path.is_file():
                    found.append(path.relative_to(files._root).as_posix())
        else:
            found.append(pattern)
    # Stable and unique: a file named by two globs is checked once.
    return sorted(dict.fromkeys(found))


def collect_declaration_issues(
    *, repo_root: Path, live_documents: Mapping[str, list[str]]
) -> list[IntegrityIssue]:
    """Run every declared check and return the diagnostics in a stable order."""
    declarations = load_declarations(repo_root)
    if not declarations:
        return []

    # The table names too. A misspelled [[ancor]] parses as valid TOML, is
    # never read, and leaves the gate green with one fewer check running.
    known_tables = set(_DECLARATION_SCHEMA) | set(_TOP_LEVEL_SCHEMA)
    known_tables.discard("site")
    for table in declarations:
        if table not in known_tables:
            raise DeclarationError(
                f"{DECLARATIONS_FILENAME} has an unknown table {table!r}. "
                f"Known tables: {', '.join(sorted(known_tables))}."
            )
    _validate_options(declarations.get("options", {}))

    files = _Files(repo_root, live_documents)
    issues: list[IntegrityIssue] = []
    issues.extend(check_values(files, declarations.get("value", [])))
    issues.extend(check_anchors(files, declarations.get("anchor", [])))
    options = declarations.get("options", {})
    issues.extend(
        check_retired(
            files,
            declarations.get("retired", []),
            strikethrough_exempt=options.get(
                "strikethrough_exempt", DEFAULT_STRIKETHROUGH_EXEMPT
            ),
        )
    )
    return sorted(issues, key=lambda issue: (issue.path, issue.line or 0, issue.code))
