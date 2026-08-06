"""Section 3 parsing must tolerate ordinary prose and the bold label style."""

from pathlib import Path

import pytest

from scripts.dev.worktree_guard import BatchBranch, GuardError, parse_batch_branch

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
ACTIVE = "- **Batch 21 is active.** Branch: `wip/batch-21`."


def _playbook(section_three: str) -> str:
    """Wrap controlled Section 3 content in a minimal PLAYBOOK document."""
    return (
        "# PLAYBOOK\n\n## 3. Active batch + next action\n\n"
        f"{section_three}\n\n## 4. Execution log\n"
    )


@pytest.mark.parametrize(
    "extra",
    [
        "- Batch 22 WP-1 is in progress.",
        "- The current batch is active until WP-8 lands.",
        "- Batch 21 rollout is in-progress on staging.",
        "- **Next action:** confirm Branch: `wip/batch-21` is clean.",
    ],
    ids=("wp-progress", "generic-current", "rollout", "repeated-branch"),
)
def test_supporting_prose_does_not_block_the_bootstrap(extra):
    """Narrative lines beside a valid declaration must not fail closed."""
    assert parse_batch_branch(_playbook(f"{ACTIVE}\n{extra}")) == BatchBranch(
        21, "wip/batch-21"
    )


@pytest.mark.parametrize(
    "branch_line",
    [
        "  Branch: `wip/batch-21`.",
        "  **Branch:** `wip/batch-21`.",
        "  **Branch**: `wip/batch-21`.",
    ],
    ids=("plain", "bold-label", "bold-word"),
)
def test_branch_metadata_accepts_the_documented_bold_style(branch_line):
    """Every other Section 3 label is bold, so Branch may be bold too."""
    playbook = _playbook(f"- **Batch 21 is active.**\n{branch_line}")
    assert parse_batch_branch(playbook) == BatchBranch(21, "wip/batch-21")


@pytest.mark.parametrize(
    ("section_three", "message"),
    [
        (
            "- **Batch 21 is active.**\n  Branch: `wip/batch-21`.\n"
            "  Branch: `wip/other`.",
            "branch",
        ),
        ("- **Batch twenty-one is active.**", "active batch"),
    ],
    ids=("conflicting-branches", "unparseable-identifier"),
)
def test_genuinely_ambiguous_metadata_still_fails_closed(section_three, message):
    """Tolerating prose must not weaken the real ambiguity guarantees."""
    with pytest.raises(GuardError, match=message):
        parse_batch_branch(_playbook(section_three))


def test_the_repository_playbook_parses():
    """The live document must never be one ordinary edit from blocking work."""
    playbook = (REPOSITORY_ROOT / "PLAYBOOK.md").read_text(encoding="utf-8")
    assert parse_batch_branch(playbook).expected_branch == "wip/batch-21"
