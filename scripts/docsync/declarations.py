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

from docsync.models import IntegrityIssue

#: Where the repository's own declarations live, relative to the repo root.
DECLARATIONS_FILENAME = ".docsync.toml"

#: A heading in a Markdown document: one to six hashes, then the text.
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")

#: An ordered-list item at the start of a line: "3. **Something**".
_LIST_ITEM_RE = re.compile(r"^(\d+)\.\s")

#: A bold lead-in used as a section marker: "**Wordmark animation** ...".
#: docs/design/README.md labels its sections this way rather than with
#: hashes, and a citation of one is a citation of a real place in the file.
_BOLD_LABEL_RE = re.compile(r"^\*\*([^*]+?)\*\*")

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


class DeclarationError(RuntimeError):
    """The declarations file itself is wrong, so no check could run.

    Kept separate from a check failing. A malformed declaration is a defect in
    the gate, and reporting it as a document problem would send the reader to
    edit the wrong file.
    """


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
    for declaration in declarations:
        name = declaration.get("name", "<unnamed>")
        sites = declaration.get("sites", [])
        if len(sites) < 2:
            raise DeclarationError(
                f"value {name!r} declares {len(sites)} site(s); "
                f"a value written in one place cannot disagree with itself"
            )

        captured: list[tuple[str, str]] = []
        for site in sites:
            rel_path = site["file"]
            lines = files.lines(rel_path)
            if lines is None:
                issues.append(_missing_file_issue("DOC009", rel_path, name))
                continue

            pattern = _compile(site["pattern"], f"value {name!r}")
            match = None
            line_number = None
            for index, line in enumerate(lines, start=1):
                match = pattern.search(line)
                if match:
                    line_number = index
                    break

            if match is None:
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

            if match.groups():
                captured.append((rel_path, match.group(1)))
                declaration.setdefault("_lines", {})[rel_path] = line_number

        if len(captured) > 1:
            distinct = {value for _path, value in captured}
            if len(distinct) > 1:
                reported = ", ".join(f"{path} says {value}" for path, value in captured)
                first_path = captured[0][0]
                issues.append(
                    _issue(
                        "DOC009",
                        first_path,
                        declaration.get("_lines", {}).get(first_path),
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
    for declaration in declarations:
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
            for line_number, line in enumerate(lines, start=1):
                for match in pattern.finditer(line):
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
    for declaration in declarations:
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

            for line_number, line in enumerate(lines, start=1):
                if exempt_from is not None and line_number >= exempt_from:
                    break
                match = pattern.search(line)
                if match and skip_struck and _is_struck_through(line, match.start()):
                    continue
                if match:
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


# ----------------------------------------------------------------------
# Shared
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
