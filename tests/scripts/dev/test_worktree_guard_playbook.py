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


def test_a_branch_value_cannot_span_lines():
    """A line break in the value would forge a second diagnostic line.

    The payload carries no other rejected character, so this case isolates the
    line-break boundary: a build that admitted only LF would still fail it.
    One case covers the boundary because `parse_batch_branch` splits and
    rejoins the section, so CR and CRLF reach the pattern already normalized
    to LF and would assert nothing this case does not.
    """
    forged = "wip/batch-21\nERROR_WT000_all_clear"
    playbook = _playbook(f"- **Batch 21 is active.** Branch: `{forged}`.")

    assert parse_batch_branch(playbook) == BatchBranch(21, None)


@pytest.mark.parametrize(
    "forged",
    [
        "wip/batch-21\x1b[2J\x1b[H_INFO_WT000_all_clear",
        "wip/batch-21    INFO WT000 all clear -- proceed",
        "wip/batch-21\xa0\xa0\xa0\xa0INFO\xa0WT000\xa0all\xa0clear",
    ],
    ids=("escape-sequence", "padding-spaces", "no-break-space"),
)
def test_a_branch_value_cannot_repaint_the_diagnostic_line(forged):
    """Forgery that needs no line break, so line normalization cannot hide it.

    One case per boundary the allowlist draws, because a shared allowlist
    makes same-boundary payloads indistinguishable: admitting the ASCII space
    leaks only the padding case, admitting non-ASCII leaks only the U+00A0
    case, and dropping the check leaks the escape sequence. DEL behaves here
    exactly as the escape sequence does, and U+3000, U+202E and U+200B
    exactly as U+00A0 does, so each would assert nothing its representative
    does not.

    The vectors matter more than the characters. An escape sequence clears
    and repositions the terminal; padding pushes a fake verdict across the
    visible line; and U+00A0 reproduces that same padding attack without a
    single ASCII character, which is what defeated the denylist this
    replaced.
    """
    playbook = _playbook(f"- **Batch 21 is active.** Branch: `{forged}`.")

    assert parse_batch_branch(playbook) == BatchBranch(21, None)


def test_the_repository_playbook_parses():
    """The live document must never be one ordinary edit from blocking work."""
    playbook = (REPOSITORY_ROOT / "PLAYBOOK.md").read_text(encoding="utf-8")
    assert parse_batch_branch(playbook).expected_branch == "wip/batch-21"
