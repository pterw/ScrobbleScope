"""Bounded, paginated Markdown archives with tracked cold storage.

History is kept, not trimmed. The existing archive paths stay the entry
points readers and links already use; when a corpus outgrows a single file
that entry point becomes an index over deterministically numbered pages, and
the pages -- hot and cold alike -- stay searchable Markdown inside the
repository.

Two properties carry the safety of this module. Flattening any archive, in
any layout, yields the same logical text: a legacy monolith, a hot index, and
an index whose oldest pages have moved to `cold/` all read identically, so
pagination can never change which entry is authoritative. And planning is
idempotent: re-running it over its own output produces no further writes, so
a repeated fix or migration cannot churn the corpus.

Cold migration never consults the wall clock. It happens only when a caller
supplies an explicit ISO as-of date, because ordinary checks and commits must
not silently relocate files just because a day has passed.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

# The thresholds arrive from `declarations`, which owns them because it must
# also validate and default the `[archives]` table. Importing them here rather
# than repeating the literals keeps one number in one place:
# `config/docsync.toml`, the default, and these signatures cannot drift
# apart. The dependency runs
# this way, not the reverse, because `declarations` is the lighter module --
# it reads TOML and text, while this one also needs the transaction layer.
from docsync.declarations import (
    DEFAULT_ARCHIVE_COLD_DAYS,
    DEFAULT_ARCHIVE_MAX_LINES,
)
from docsync.markdown import prose_lines
from docsync.models import IntegrityIssue, SyncError
from docsync.transaction import resolve_within

#: The machine manifest is wrapped in an HTML comment so it is invisible in
#: rendered Markdown and invisible to the shared prose scanner: no reader and
#: no other check can mistake the index's bookkeeping for archive content.
INDEX_START_MARKER = "<!-- DOCSYNC:ARCHIVE-INDEX v1 -->"
INDEX_END_MARKER = "<!-- DOCSYNC:ARCHIVE-INDEX-END -->"

#: Each page announces itself, so a page opened on its own says what it is
#: and a reader can find its index.
PAGE_MARKER = "<!-- DOCSYNC:ARCHIVE-PAGE v1 -->"

#: Marker, title, blank. Counted against the page target, because the target
#: bounds the rendered file a reader actually opens.
PAGE_HEADER_LINES = 3

#: Version 1 numbered pages in reading order, so page 0001 held the newest
#: entries. Version 2 numbers them chronologically, so page 0001 holds the
#: oldest and never changes again. The two cannot be told apart by reading a
#: page -- both are well-formed Markdown -- so a v1 index read as v2 comes
#: back with its entries reordered and would be written back that way. The
#: version is what makes that a refusal instead of a silent rewrite.
MANIFEST_VERSION = 2

HOT_DIRECTORY = "pages"
COLD_DIRECTORY = "cold"

#: An entry begins at a real level-2 or level-3 heading. Level 2 matters: a
#: findings archive separates rotations with `## Rotated <date>` banners, and
#: treating one as an entry keeps it a whole, unsplittable block instead of
#: letting a page boundary strand it from nothing or glue it to a neighbour.
ENTRY_BOUNDARY_RE = re.compile(r"^#{2,3}\s")

#: The three explicit date spellings this corpus uses. Nothing else is read
#: as a date: an entry whose age cannot be known must stay undated rather
#: than be assigned an invented one, because an invented date decides
#: whether history moves to cold storage.
_DATE_PATTERNS = (
    re.compile(r"^###\s+(\d{4}-\d{2}-\d{2})\s+-\s"),
    re.compile(r"^\s*(?:[-*+]\s+)?\*\*Completed:\*\*\s*(\d{4}-\d{2}-\d{2})\s*$"),
    re.compile(r"^##\s+Rotated\s+(\d{4}-\d{2}-\d{2})\b"),
)


def structure_issue(path: str, error: SyncError) -> IntegrityIssue:
    """Report one archive-layout failure as the gate's DOC020 diagnostic.

    Everything this module refuses -- a page an index names but nobody wrote,
    a manifest that does not parse, a page missing its header, a managed page
    no index references, a symlink inside the tree -- is raised as a
    ``SyncError`` because the reading code has no business deciding what a
    caller should do about it. The gate does have that business: a reader who
    runs `--check` needs the diagnostic beside DOC001 and DOC019, with the
    path and the repair, rather than a traceback or a bare exit 2 that reads
    as "the tool broke".

    The remediation never proposes an automatic repair. Every one of these
    states is a disagreement between an index and the files beside it, and the
    two sides are equally plausible: deleting the page the index does not name
    loses history, and rewriting the index to match the files loses the record
    that the page existed. Only a reader knows which happened.
    """
    return IntegrityIssue(
        code="DOC020",
        severity="error",
        path=path,
        line=None,
        invariant=("The archive's pages on disk match the index that enumerates them."),
        remediation=(
            f"{error} Restore the missing side from Git history, or correct the "
            f"index by hand; docsync will not guess which side of the "
            f"disagreement is the history worth keeping."
        ),
    )


def _page_target_issue(path: str, max_lines: int) -> IntegrityIssue:
    """Report an unpaginated archive that has outgrown its page target.

    Reported at warning severity, never error: pagination is an explicit
    maintenance action (``--paginate-archives``), not something an ordinary
    `--check` or `--fix` performs as a side effect. This diagnostic only
    names the condition; it writes nothing.
    """
    return IntegrityIssue(
        code="DOC024",
        severity="warning",
        path=path,
        line=None,
        invariant=(
            "An archive under its page target of "
            f"{max_lines} lines stays a single file; once its logical text "
            "exceeds that target it is paginated explicitly, never as a "
            "side effect of --check or --fix."
        ),
        remediation=(
            f"{path} has grown past the {max_lines}-line page target. Run "
            "`python scripts/doc_state_sync.py --paginate-archives` to split "
            "it into indexed, numbered pages. This warning writes nothing on "
            "its own."
        ),
    )


def _never_ageing_page_issue(path: str, page_name: str) -> IntegrityIssue:
    """Report a finalized page that the cold-storage rule can never age.

    `_age` only moves a finalized, non-oversized, hot page to cold storage
    when every entry on it carries an explicit date before the cutoff. A
    page holding even one undated entry can never satisfy that rule, no
    matter how old the page itself is -- so this is reported once per such
    page, at warning severity, purely informational.
    """
    return IntegrityIssue(
        code="DOC024",
        severity="warning",
        path=path,
        line=None,
        invariant=(
            "A finalized page moves to cold storage only when every entry "
            "on it carries a date before the cutoff; a page with even one "
            "undated entry can never satisfy that rule."
        ),
        remediation=(
            f"Page {page_name} holds at least one entry with no explicit "
            "date, so it can never age into cold storage. This is "
            "informational only: add an explicit date to every entry on the "
            "page if it should become cold-storage eligible."
        ),
    )


def _strip_trailing_blank(lines: Sequence[str]) -> list[str]:
    block = list(lines)
    while block and not block[-1].strip():
        block.pop()
    return block


def _split(text: str) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    """Split logical archive text into its prologue and its whole entries."""
    lines = text.split("\n")
    starts = [
        index for index, line in prose_lines(lines) if ENTRY_BOUNDARY_RE.match(line)
    ]
    first = starts[0] if starts else len(lines)
    prologue = tuple(_strip_trailing_blank(lines[:first]))
    entries = tuple(
        tuple(
            _strip_trailing_blank(
                lines[
                    start : starts[position + 1]
                    if position + 1 < len(starts)
                    else len(lines)
                ]
            )
        )
        for position, start in enumerate(starts)
    )
    return prologue, entries


def _join(prologue: Sequence[str], entries: Sequence[Sequence[str]]) -> str:
    """Render a prologue and entries back into one canonical logical text."""
    blocks = []
    if prologue:
        blocks.append("\n".join(prologue))
    blocks.extend("\n".join(entry) for entry in entries)
    return "\n\n".join(blocks) + "\n" if blocks else ""


def normalize(text: str) -> str:
    """Return the canonical rendering of one archive's logical text."""
    prologue, entries = _split(text)
    return _join(prologue, entries)


def _entry_date(entry: Sequence[str]) -> dt.date | None:
    """Return the entry's newest explicit date, or None when it has none."""
    found: list[dt.date] = []
    for line in entry:
        for pattern in _DATE_PATTERNS:
            match = pattern.match(line)
            if match is None:
                continue
            try:
                found.append(dt.date.fromisoformat(match.group(1)))
            except ValueError:
                # An impossible calendar date is not a date. Treating it as
                # one would let a typo age a page into cold storage.
                continue
    return max(found) if found else None


def _page_line_count(entries: Sequence[Sequence[str]]) -> int:
    """Rendered line count of a page holding ``entries``, headers included."""
    if not entries:
        return PAGE_HEADER_LINES
    bodies = sum(len(entry) for entry in entries)
    return PAGE_HEADER_LINES + bodies + (len(entries) - 1)


@dataclasses.dataclass(frozen=True)
class _Page:
    """One numbered archive page and where it currently lives."""

    number: int
    name: str
    location: str
    oversized: bool
    entries: tuple[tuple[str, ...], ...]


@dataclasses.dataclass(frozen=True)
class _Layout:
    """The archive as it exists on disk right now.

    Pages are held in chronological order: page 0001 holds the oldest
    entries and never changes again, and the highest-numbered page is the
    writable tail new entries land on. Logical archive text runs the other
    way, newest first, because that is how these archives are read. The two
    orders meet here and in `plan`, and nowhere else.
    """

    paginated: bool
    prologue: tuple[str, ...]
    pages: tuple[_Page, ...]

    @property
    def entries(self) -> tuple[tuple[str, ...], ...]:
        """Return the archive's entries as logical text orders them."""
        chronological = (entry for page in self.pages for entry in page.entries)
        return tuple(reversed(tuple(chronological)))


class ArchiveStore:
    """Reads and plans one repository archive tree rooted at ``root``."""

    def __init__(self, root: Path, max_lines: int = DEFAULT_ARCHIVE_MAX_LINES) -> None:
        self.root = Path(root).resolve()
        if max_lines <= PAGE_HEADER_LINES:
            raise SyncError(
                f"An archive page target of {max_lines} lines cannot hold a "
                f"page header of {PAGE_HEADER_LINES} lines."
            )
        self.max_lines = max_lines

    # -- paths ------------------------------------------------------------

    def page_path(self, index_path: Path, page: Mapping[str, object] | _Page) -> Path:
        """Return the contained on-disk path of one indexed page.

        Pages live beside their own index, not at ``self.root``: a store can
        be asked to plan several archives that live in different
        subdirectories of a shared root (the real topology --
        `docs/history/findings/` and `docs/logarchive/` are different
        directories), and each index's `pages/`/`cold/` trees must not
        collide with, or escape into, a neighbour's.
        """
        if isinstance(page, _Page):
            name, location = page.name, page.location
        else:
            name = str(page["name"])
            location = str(page.get("location", "hot"))
        if location not in ("hot", "cold"):
            raise SyncError(f"Unknown archive page location {location!r}.")
        directory = COLD_DIRECTORY if location == "cold" else HOT_DIRECTORY
        # `index_path` is always already resolved under `self.root` by the
        # caller (via `resolve_within` in `plan`/`read`), so its parent is
        # guaranteed contained too -- one containment check against the
        # shared root is enough, and it lets a not-yet-created subdirectory
        # resolve without requiring it to exist first.
        candidate = Path(index_path).parent / directory / name
        return resolve_within(self.root, candidate)

    def _managed_name_re(self, stem: str) -> re.Pattern[str]:
        # Scoped to this archive's own stem: `docs/history/logs/` holds one
        # archive per batch, so a neighbour's pages are not this archive's
        # orphans.
        return re.compile(rf"^{re.escape(stem)}_\d{{4}}\.md$")

    # -- reading ----------------------------------------------------------

    def _read_page(self, path: Path) -> tuple[tuple[str, ...], ...]:
        """Return one page's entries, refusing to lose anything silently.

        A page this store wrote always starts with `PAGE_MARKER` and holds
        nothing but its three-line header before the first entry heading.
        Either violation -- a missing header, or extra content the header
        strip would otherwise discard -- must be reported: the next
        `plan()`/`publish()` cycle would write the truncated page back
        permanently, turning a silent read into a silent, irreversible
        edit.
        """
        lines = path.read_text(encoding="utf-8").split("\n")
        if not lines or lines[0].strip() != PAGE_MARKER:
            raise SyncError(
                f"Archive page {path} does not start with the required "
                f"{PAGE_MARKER!r} header."
            )
        body = lines[PAGE_HEADER_LINES:]
        prologue, entries = _split("\n".join(body))
        if prologue:
            raise SyncError(
                f"Archive page {path} has content before its first entry "
                f"heading that a plain read would discard: {prologue[0]!r}"
            )
        # Written newest first for readers, held oldest first internally.
        return tuple(reversed(entries))

    def _load(self, index_path: Path) -> _Layout:
        """Parse and validate the archive's current layout."""
        if not index_path.is_file():
            # A missing index is not necessarily a fresh archive: it may be
            # a hand-deleted or moved entry point that still has managed
            # pages sitting beside it. Those pages must be reported, never
            # silently treated as orphans of a brand-new empty layout --
            # `plan()`'s single-monolith path would otherwise schedule every
            # one of them, hot and cold alike, for deletion.
            self._reject_orphans(index_path, set())
            return _Layout(paginated=False, prologue=(), pages=())
        text = index_path.read_text(encoding="utf-8")
        if INDEX_START_MARKER not in text:
            # A legacy monolith may not have managed pages beside it. That
            # state is precisely the one the specification forbids -- a whole
            # body and a paginated copy, each claiming to be authoritative --
            # and it must be reported, never resolved by deleting one side.
            self._reject_orphans(index_path, set())
            prologue, entries = _split(text)
            # Pages hold entries oldest first whatever the layout, so that
            # `_Layout.entries` has exactly one rule to undo.
            page = _Page(0, index_path.name, "hot", False, tuple(reversed(entries)))
            return _Layout(paginated=False, prologue=prologue, pages=(page,))

        head, _, rest = text.partition(INDEX_START_MARKER)
        body, terminator, _ = rest.partition(INDEX_END_MARKER)
        if not terminator:
            raise SyncError(
                f"The archive manifest in {index_path} is not terminated by "
                f"{INDEX_END_MARKER}."
            )
        payload = body.strip()
        if payload.startswith("<!--") and payload.endswith("-->"):
            payload = payload[4:-3].strip()
        try:
            manifest = json.loads(payload)
            version = int(manifest["version"])
            listed = list(manifest["pages"])
        except (ValueError, KeyError, TypeError) as error:
            raise SyncError(
                f"Unreadable archive manifest in {index_path}: {error}"
            ) from None
        if version == 1:
            raise SyncError(
                f"The archive index {index_path} was paginated by an earlier "
                f"docsync that numbered pages newest first; this tool numbers "
                f"them oldest first. Reading it here would reorder its "
                f"entries. Concatenate its pages back into a single "
                f"{index_path.name}, newest entry first, delete the page "
                f"directories beside it, and let `--paginate-archives` "
                f"rebuild the index."
            )
        if version != MANIFEST_VERSION:
            raise SyncError(
                f"The archive manifest in {index_path} declares unsupported "
                f"version {version}; this tool writes version "
                f"{MANIFEST_VERSION}."
            )

        pages: list[_Page] = []
        seen: set[str] = set()
        for position, record in enumerate(listed, start=1):
            try:
                name = str(record["name"])
                location = str(record["location"])
                oversized = bool(record["oversized"])
            except (KeyError, TypeError) as error:
                raise SyncError(
                    f"Incomplete archive page record in {index_path}: {error}"
                ) from None
            if name in seen:
                raise SyncError(
                    f"{index_path} references archive page {name} more than once."
                )
            seen.add(name)
            path = self.page_path(index_path, record)
            if not path.is_file():
                raise SyncError(f"Indexed archive page is missing: {path}")
            number = self._page_number(index_path.stem, name, position)
            pages.append(
                _Page(number, name, location, oversized, self._read_page(path))
            )

        self._reject_orphans(index_path, seen)
        prologue = tuple(_strip_trailing_blank(head.split("\n")))
        return _Layout(paginated=True, prologue=prologue, pages=tuple(pages))

    def _page_number(self, stem: str, name: str, fallback: int) -> int:
        match = re.fullmatch(rf"{re.escape(stem)}_(\d{{4}})\.md", name)
        return int(match.group(1)) if match else fallback

    def _reject_orphans(self, index_path: Path, referenced: set[str]) -> None:
        # `index_path` is always already resolved under `self.root` by the
        # caller, so its parent needs no separate containment check here.
        managed = self._managed_name_re(index_path.stem)
        for directory in (HOT_DIRECTORY, COLD_DIRECTORY):
            folder = index_path.parent / directory
            if folder.is_symlink():
                raise SyncError(
                    f"Refusing to follow a symlink inside the archive: {folder}"
                )
            if not folder.is_dir():
                continue
            for candidate in sorted(folder.iterdir()):
                if managed.match(candidate.name) and candidate.name not in referenced:
                    raise SyncError(
                        f"Managed archive page {candidate} is not referenced by "
                        f"{index_path}. Restore the reference or remove the file; "
                        f"an unreferenced page is unreachable history."
                    )

    def read(self, path: Path) -> str:
        """Return one archive's logical text, whatever its physical layout."""
        index_path = resolve_within(self.root, path)
        if not index_path.is_file():
            raise SyncError(f"Archive entry point does not exist: {index_path}")
        layout = self._load(index_path)
        return _join(layout.prologue, layout.entries)

    def page_target_issues(self, path: Path) -> list[IntegrityIssue]:
        """Return this archive's DOC024 page-target diagnostics, if any.

        Two independent conditions are checked, both warning-only so
        `--check` still exits 0 on them. An unpaginated (legacy monolith)
        archive whose logical text has outgrown `max_lines` warns once,
        naming the explicit `--paginate-archives` maintenance command --
        pagination is never triggered as a side effect of reading. A
        paginated archive's finalized, non-oversized, hot page whose entries
        are not all dated warns once as well, because `_age` requires every
        entry on such a page to carry a date before the cutoff: a page
        missing even one date can never satisfy that rule, whatever the
        cutoff turns out to be.

        A missing entry point yields no diagnostics: an archive that has
        not been created yet has nothing to warn about.
        """
        index_path = resolve_within(self.root, path)
        if not index_path.is_file():
            return []
        relative = index_path.relative_to(self.root).as_posix()
        layout = self._load(index_path)

        if not layout.paginated:
            flattened = _join(layout.prologue, layout.entries)
            if len(flattened.splitlines()) > self.max_lines:
                return [_page_target_issue(relative, self.max_lines)]
            return []

        issues: list[IntegrityIssue] = []
        total = len(layout.pages)
        for position, page in enumerate(layout.pages):
            finalized = position < total - 1
            if not finalized or page.oversized or page.location != "hot":
                continue
            if not page.entries:
                continue
            dates = [_entry_date(entry) for entry in page.entries]
            if not all(date is not None for date in dates):
                issues.append(_never_ageing_page_issue(relative, page.name))
        return issues

    # -- planning ---------------------------------------------------------

    def _pack(
        self, stem: str, entries: Sequence[Sequence[str]], start: int
    ) -> list[_Page]:
        """Greedily fill pages without ever splitting an entry."""
        pages: list[_Page] = []
        number = start
        current: list[tuple[str, ...]] = []

        def close(block: list[tuple[str, ...]], oversized: bool) -> None:
            nonlocal number
            pages.append(
                _Page(
                    number,
                    f"{stem}_{number:04d}.md",
                    "hot",
                    oversized,
                    tuple(block),
                )
            )
            number += 1

        for raw in entries:
            entry = tuple(raw)
            if current and _page_line_count([*current, entry]) > self.max_lines:
                close(current, False)
                current = []
            if not current and _page_line_count([entry]) > self.max_lines:
                # No truncation and no split: the entry gets a page of its
                # own, and the index says why that page breaks the target.
                close([entry], True)
                continue
            current.append(entry)
        if current:
            close(current, False)
        return pages

    def _render_page(self, stem: str, page: _Page) -> bytes:
        header = [PAGE_MARKER, f"# {stem} -- page {page.number:04d}", ""]
        body: list[str] = []
        # Held oldest first, written newest first: a page reads the same way
        # the archive it belongs to does. `_read_page` undoes this.
        for position, entry in enumerate(reversed(page.entries)):
            if position:
                body.append("")
            body.extend(entry)
        return ("\n".join(header + body) + "\n").encode("utf-8")

    def _render_index(self, prologue: Sequence[str], pages: Sequence[_Page]) -> bytes:
        manifest = {
            "version": MANIFEST_VERSION,
            "pages": [
                {
                    "name": page.name,
                    "location": page.location,
                    "entries": len(page.entries),
                    "lines": _page_line_count(page.entries),
                    "oversized": page.oversized,
                }
                for page in pages
            ],
        }
        lines = list(_strip_trailing_blank(prologue))
        lines += [
            "",
            INDEX_START_MARKER,
            "<!-- " + json.dumps(manifest, separators=(",", ":")) + " -->",
            INDEX_END_MARKER,
            "",
            "## Archive pages",
            "",
            "Every entry in this archive lives on exactly one page below.",
            "Pages run oldest first: the last one listed holds the newest",
            "entries and is the only one that still changes.",
            "",
        ]
        for page in pages:
            directory = COLD_DIRECTORY if page.location == "cold" else HOT_DIRECTORY
            notes = []
            if page.location == "cold":
                notes.append("cold storage")
            if page.oversized:
                notes.append("oversized: one indivisible entry exceeds the page target")
            suffix = f" ({'; '.join(notes)})" if notes else ""
            reference = f"{directory}/{page.name}"
            lines.append(
                f"- [{reference}]({reference}) -- {len(page.entries)} entries, "
                f"{_page_line_count(page.entries)} lines{suffix}"
            )
        return ("\n".join(lines) + "\n").encode("utf-8")

    def _diff(
        self, index_path: Path, desired: dict[Path, bytes]
    ) -> dict[Path, bytes | None]:
        """Reduce a full candidate corpus to the changes it actually makes."""
        updates: dict[Path, bytes | None] = {
            path: payload
            for path, payload in desired.items()
            if not path.is_file() or path.read_bytes() != payload
        }
        managed = self._managed_name_re(index_path.stem)
        for directory in (HOT_DIRECTORY, COLD_DIRECTORY):
            folder = index_path.parent / directory
            if not folder.is_dir() or folder.is_symlink():
                continue
            for candidate in sorted(folder.iterdir()):
                if managed.match(candidate.name) and candidate not in desired:
                    updates[candidate] = None
        return updates

    def plan(
        self,
        path: Path,
        text: str,
        *,
        as_of: dt.date | None = None,
        cold_days: int = DEFAULT_ARCHIVE_COLD_DAYS,
    ) -> dict[Path, bytes | None]:
        """Compute the writes that put ``text`` into this archive's layout.

        ``as_of`` is the whole cold-storage trigger. Left at None -- which is
        what an ordinary check or commit passes -- no file is aged and
        nothing moves beneath `cold/`, regardless of how old its entries are.
        Only an explicit maintenance date evaluates eligibility.
        """
        index_path = resolve_within(self.root, path)
        layout = self._load(index_path)
        prologue, entries = _split(text)
        flattened = _join(prologue, entries)

        # Pagination is one-way. A monolith that still fits stays a monolith,
        # but an archive that has already become an index stays one even if a
        # later edit shrinks it: collapsing back would move every entry
        # between files on each side of the threshold, and the churn would
        # rewrite history no one changed.
        if not layout.paginated and len(flattened.splitlines()) <= self.max_lines:
            return self._diff(index_path, {index_path: flattened.encode("utf-8")})

        # Entries arrive newest first, because that is how the archive reads,
        # but pages are numbered oldest first so that a finalized page keeps
        # its number and its bytes forever. Every producer of this text sorts
        # newest first and so prepends, which means matching pages in text
        # order would miss on the very first page of every run and repack the
        # whole archive each time an entry rotated.
        chronological = tuple(reversed(entries))

        existing = list(layout.pages) if layout.paginated else []
        retained: list[_Page] = []
        cursor = 0
        for page in existing:
            size = len(page.entries)
            if tuple(chronological[cursor : cursor + size]) != page.entries:
                break
            retained.append(page)
            cursor += size

        leftover: list[Sequence[str]] = list(chronological[cursor:])
        if (
            leftover
            and retained
            and retained[-1] is existing[-1]
            and retained[-1].location == "hot"
            and not retained[-1].oversized
        ):
            # The last page is the writable tail: it keeps its number and
            # receives new entries until it reaches the target, so finalized
            # pages are never renumbered merely because entries arrived.
            tail = retained.pop()
            leftover = list(tail.entries) + leftover
            start = tail.number
        else:
            start = retained[-1].number + 1 if retained else 1

        pages = retained + self._pack(index_path.stem, leftover, start)
        if as_of is not None:
            pages = self._age(pages, as_of, cold_days)

        desired: dict[Path, bytes] = {
            self.page_path(index_path, page): self._render_page(index_path.stem, page)
            for page in pages
        }
        desired[index_path] = self._render_index(prologue, pages)
        return self._diff(index_path, desired)

    def _age(
        self, pages: Sequence[_Page], as_of: dt.date, cold_days: int
    ) -> list[_Page]:
        """Mark every finalized, fully dated, wholly old page cold."""
        cutoff = as_of - dt.timedelta(days=cold_days)
        aged: list[_Page] = []
        for position, page in enumerate(pages):
            location = page.location
            finalized = position < len(pages) - 1
            if finalized and not page.oversized and location == "hot":
                dates = [_entry_date(entry) for entry in page.entries]
                if dates and all(
                    value is not None and value < cutoff for value in dates
                ):
                    location = "cold"
            aged.append(dataclasses.replace(page, location=location))
        return aged
