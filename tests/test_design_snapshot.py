"""Guard the verbatim design import against in-place edits.

The 61 design-project files under `docs/design/` are a byte-for-byte snapshot
imported by `b4e23bf`; `f857ac2` later corrected the location of `styles.css`
without changing its bytes. Their value is that they can disagree with the
implementation. An agent that edits the snapshot to match the code silently
removes the only independent check on the code. Overrides belong in the
repository-owned `docs/design/RECONCILIATION.md`, which is excluded here.

To change a digest here you must be re-importing from the design project, not
reconciling with the repository.
"""

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_ROOT = REPO_ROOT / "docs" / "design"
REPOSITORY_OWNED_PATHS = frozenset({"RECONCILIATION.md"})

#: Aggregate manifest of every imported path and byte. Update ONLY on a fresh
#: import from the design project.
SNAPSHOT_FILE_COUNT = 61
SNAPSHOT_TREE_DIGEST = (
    "0c60b0316d3df661e3004ad4454c43c325d87bfc794596e023029eacaa5bedb7"
)


def _snapshot_tree_digest() -> tuple[int, str]:
    """Hash the complete imported manifest with stable, unambiguous framing.

    Relative POSIX paths make the digest platform-independent. Length prefixes
    keep path and content boundaries unambiguous, so a rename, add, deletion,
    or byte edit changes the aggregate even when the remaining files match.
    """
    paths = sorted(
        (
            path
            for path in SNAPSHOT_ROOT.rglob("*")
            if path.is_file()
            and path.relative_to(SNAPSHOT_ROOT).as_posix() not in REPOSITORY_OWNED_PATHS
        ),
        key=lambda path: path.relative_to(SNAPSHOT_ROOT).as_posix(),
    )
    digest = hashlib.sha256()
    for path in paths:
        relative_bytes = path.relative_to(SNAPSHOT_ROOT).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative_bytes).to_bytes(4, "big"))
        digest.update(relative_bytes)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return len(paths), digest.hexdigest()


def test_imported_design_tree_is_unedited() -> None:
    """Every imported design path and byte must match the guarded manifest."""
    actual = _snapshot_tree_digest()
    expected = (SNAPSHOT_FILE_COUNT, SNAPSHOT_TREE_DIGEST)
    assert actual == expected, (  # nosec B101 - pytest rewrites assertions.
        f"docs/design snapshot changed: expected {expected}, got {actual}. "
        "Record repository overrides in docs/design/RECONCILIATION.md, or "
        "update this manifest only when re-importing from the design project."
    )
