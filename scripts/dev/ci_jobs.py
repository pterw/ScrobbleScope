"""Decisions the CI workflow delegates to Python so they can be tested.

``docs-only`` reads NUL-separated changed paths on stdin and prints ``true``
when every path is documentation (a pull request that can skip the browser
job), else ``false``. ``aggregate`` turns the ``needs.*.result`` values into
the one verdict the required ``quality-gate`` check reports. Both fail closed.
"""

from __future__ import annotations

import argparse
import sys

DOCS_PREFIXES = ("docs/", ".superpowers/")
DOCS_FILES = ("config/docsync.toml",)
DOCS_SUFFIX = ".md"


def _is_docs_path(path: str) -> bool:
    return (
        path.startswith(DOCS_PREFIXES)
        or path in DOCS_FILES
        or path.endswith(DOCS_SUFFIX)
    )


def docs_only(raw: bytes) -> bool:
    """True when the NUL-separated paths are non-empty and all documentation."""
    paths = [p.decode("utf-8", "surrogateescape") for p in raw.split(b"\0") if p]
    return bool(paths) and all(_is_docs_path(p) for p in paths)


def aggregate(
    changes: str, checks: str, browser: str, docs_only_flag: str
) -> tuple[int, str]:
    """Return (exit code, message) for the three job results and the docs flag."""
    if docs_only_flag not in ("true", "false"):
        return 1, f"docs_only is {docs_only_flag!r}, expected 'true' or 'false'"
    if changes != "success":
        return 1, f"changes did not succeed: {changes}"
    if checks != "success":
        return 1, f"checks did not succeed: {checks}"
    if browser == "success":
        return 0, "all jobs succeeded"
    if browser == "skipped" and docs_only_flag == "true":
        return 0, "browser skipped for a docs-only pull request"
    return 1, f"browser did not succeed: {browser} (docs_only={docs_only_flag})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("docs-only")
    agg = sub.add_parser("aggregate")
    for name in ("changes", "checks", "browser", "docs-only"):
        agg.add_argument(f"--{name}", required=True)
    args = parser.parse_args(argv)
    if args.command == "docs-only":
        print("true" if docs_only(sys.stdin.buffer.read()) else "false")
        return 0
    code, message = aggregate(args.changes, args.checks, args.browser, args.docs_only)
    print(message)
    return code


if __name__ == "__main__":
    sys.exit(main())
