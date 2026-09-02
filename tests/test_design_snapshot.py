"""Guard the verbatim design import against in-place edits.

`docs/design/README.md` and the files under `docs/design/tokens/` are a
snapshot of the owner's design project, imported byte-for-byte by `b4e23bf`.
Their value is that they can disagree with the implementation. An agent that
edits the snapshot to match the code silently removes the only independent
check on the code. Overrides belong in `docs/design/RECONCILIATION.md`.

To change a digest here you must be re-importing from the design project, not
reconciling with the repository.
"""

import hashlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

#: SHA-256 of each imported file, as committed by `b4e23bf`. Update ONLY on a
#: fresh import from the design project.
SNAPSHOT_DIGESTS = {
    "docs/design/README.md": "eed192f1b272fae904d3401fe60bcab32bcfebccab425ce6d858672ca33adf6b",
}


@pytest.mark.parametrize("relative_path", sorted(SNAPSHOT_DIGESTS))
def test_imported_design_file_is_unedited(relative_path):
    """The snapshot must match its import digest byte for byte."""
    path = REPO_ROOT / relative_path
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == SNAPSHOT_DIGESTS[relative_path], (
        f"{relative_path} was edited in place. Record the override in "
        f"docs/design/RECONCILIATION.md instead, or update this digest only "
        f"when re-importing from the design project."
    )
