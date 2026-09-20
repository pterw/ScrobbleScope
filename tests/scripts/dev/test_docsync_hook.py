"""Tests for scripts/dev/install_docsync_hook.py.

Every test here builds its own throwaway Git repository under ``tmp_path``
(some with a real linked worktree via ``git worktree add``) and never
touches this repository's own ``.git``. That is a hard requirement, not a
style choice: `--install` writes a Git hook, and the only way to prove it
writes the *right* file in the *right* place without risking the real
repository is to give it a disposable one.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.dev import install_docsync_hook as installer

# --------------------------------------------------------------------- #
# Real-Git helpers                                                        #
# --------------------------------------------------------------------- #


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, (
        f"git {' '.join(args)} failed in {cwd}: {result.stderr}"
    )
    return result


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "test@example.invalid")
    _git(path, "config", "user.name", "Test")
    (path / "README.md").write_text("seed\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-q", "-m", "seed")
    return path


def _make_qualified_python(primary_root: Path) -> Path:
    venv_python = primary_root / ".venv" / "Scripts" / "python.exe"
    venv_python.parent.mkdir(parents=True, exist_ok=True)
    venv_python.write_text("", encoding="utf-8")
    return venv_python


# --------------------------------------------------------------------- #
# Primary vs. linked checkout resolution (real Git worktrees)              #
# --------------------------------------------------------------------- #


def test_primary_checkout_root_in_the_primary_checkout_is_itself(tmp_path):
    repo = _init_repo(tmp_path / "primary")
    assert installer.primary_checkout_root(repo) == repo.resolve()


def test_primary_checkout_root_from_a_linked_worktree_is_the_primary(tmp_path):
    primary = _init_repo(tmp_path / "primary")
    linked = tmp_path / "linked"
    _git(primary, "worktree", "add", "-q", str(linked), "-b", "feature")
    assert installer.primary_checkout_root(linked) == primary.resolve()


def test_list_worktrees_discloses_every_worktree_including_linked_ones(tmp_path):
    primary = _init_repo(tmp_path / "primary")
    linked = tmp_path / "linked"
    _git(primary, "worktree", "add", "-q", str(linked), "-b", "feature")

    worktrees = installer.list_worktrees(linked)
    resolved = {p.resolve() for p in worktrees}
    assert primary.resolve() in resolved
    assert linked.resolve() in resolved
    assert len(worktrees) == 2


# --------------------------------------------------------------------- #
# Hook directory resolution                                               #
# --------------------------------------------------------------------- #


def test_resolve_hook_directory_defaults_to_common_dir_hooks(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    expected = installer.git_common_dir(repo) / "hooks"
    assert installer.resolve_hook_directory(repo) == expected


def test_resolve_hook_directory_honours_configured_hooks_path(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _git(repo, "config", "core.hooksPath", ".githooks")
    assert installer.resolve_hook_directory(repo) == (repo / ".githooks").resolve()


def test_resolve_hook_directory_relative_path_resolves_per_worktree(tmp_path):
    """A *relative* core.hooksPath is resolved against each worktree's own
    root, matching AGENTS.md's "activation is per clone" note -- a linked
    worktree without its own copy of the directory gets a *different*
    resolved path than the primary checkout, not the primary's path reused.
    """
    primary = _init_repo(tmp_path / "primary")
    _git(primary, "config", "core.hooksPath", ".githooks")
    linked = tmp_path / "linked"
    _git(primary, "worktree", "add", "-q", str(linked), "-b", "feature")

    primary_hooks = installer.resolve_hook_directory(primary)
    linked_hooks = installer.resolve_hook_directory(linked)
    assert primary_hooks == (primary / ".githooks").resolve()
    assert linked_hooks == (linked / ".githooks").resolve()
    assert primary_hooks != linked_hooks


def test_resolve_hook_directory_ignores_the_callers_subdirectory(tmp_path):
    """A relative core.hooksPath resolves against the worktree root.

    Git runs hooks from the top of the working tree, so that is what a
    relative path resolves against. Every other test here passes the repo
    root as `cwd`, where the two are the same; called from a subdirectory
    they diverge, and resolving against `cwd` put the wrapper somewhere
    Git never looks while still reporting a successful install.
    """
    repo = _init_repo(tmp_path / "repo")
    _git(repo, "config", "core.hooksPath", ".githooks")
    subdirectory = repo / "scripts" / "dev"
    subdirectory.mkdir(parents=True)

    assert installer.resolve_hook_directory(subdirectory) == (
        (repo / ".githooks").resolve()
    )


def test_install_refuses_a_symlinked_hook_path(tmp_path):
    """Writing through a link would rewrite its target, not the hook."""
    repo = _init_repo(tmp_path / "repo")
    _make_qualified_python(repo)
    hooks = installer.resolve_hook_directory(repo)
    hooks.mkdir(parents=True, exist_ok=True)
    # The target must classify as *ours*, or the pre-existing-hook check
    # refuses first and this proves nothing about the symlink guard.
    target = tmp_path / "somebody-elses-file"
    target.write_text(f"#!/bin/sh\n# {installer.GENERATED_MARKER}\n", encoding="utf-8")
    original = target.read_text(encoding="utf-8")
    try:
        (hooks / "pre-commit").symlink_to(target)
    except OSError:  # pragma: no cover - unprivileged Windows
        pytest.skip("creating a symlink requires privileges here")

    messages: list[str] = []
    code = installer.install(
        repo, yes=True, os_name="nt", access=lambda *a: True, print_fn=messages.append
    )

    assert code == 2
    assert target.read_text(encoding="utf-8") == original
    assert any("symlink" in message for message in messages)


def test_resolve_hook_directory_absolute_hooks_path_is_shared(tmp_path):
    shared = tmp_path / "shared-hooks"
    repo = _init_repo(tmp_path / "repo")
    _git(repo, "config", "core.hooksPath", str(shared))
    assert installer.resolve_hook_directory(repo) == shared


# --------------------------------------------------------------------- #
# Hook classification                                                     #
# --------------------------------------------------------------------- #


def test_classify_existing_hook_absent(tmp_path):
    assert installer.classify_existing_hook(tmp_path / "missing") == "absent"


def test_classify_existing_hook_ours(tmp_path):
    hook = tmp_path / "pre-commit"
    hook.write_text(
        installer.render_hook_script(
            python_exe=Path("/venv/python"), preflight_script=Path("/repo/pre.py")
        ),
        encoding="utf-8",
    )
    assert installer.classify_existing_hook(hook) == "ours"


def test_classify_existing_hook_unknown(tmp_path):
    hook = tmp_path / "pre-commit"
    hook.write_text("#!/bin/sh\necho 'a human wrote this'\n", encoding="utf-8")
    assert installer.classify_existing_hook(hook) == "unknown"


# --------------------------------------------------------------------- #
# Generated wrapper content                                               #
# --------------------------------------------------------------------- #


def test_hook_script_runs_docsync_before_delegating_to_pre_commit():
    """docsync-first ordering: the preflight line precedes hook-impl."""
    script = installer.render_hook_script(
        python_exe=Path("/venv/python"), preflight_script=Path("/repo/pre.py")
    )
    preflight_index = script.index("pre.py")
    # rindex, not index: the header comment also mentions "pre_commit
    # hook-impl" by name while explaining the design, before any code runs.
    hook_impl_index = script.rindex("pre_commit hook-impl")
    assert preflight_index < hook_impl_index
    assert '"/venv/python" "/repo/pre.py" --staged' in script


def test_hook_script_delegates_nonrecursively():
    """Delegation goes straight to `hook-impl`, never back through git commit
    or `pre-commit run` -- either of which could re-enter hooksPath.
    """
    script = installer.render_hook_script(
        python_exe=Path("/venv/python"), preflight_script=Path("/repo/pre.py")
    )
    assert "pre_commit hook-impl" in script
    assert "git commit" not in script
    assert "pre-commit run" not in script


def test_hook_script_exits_before_delegating_on_preflight_failure():
    """The script's own control flow: nonzero preflight -> exit, never exec."""
    script = installer.render_hook_script(
        python_exe=Path("/venv/python"), preflight_script=Path("/repo/pre.py")
    )
    lines = script.splitlines()
    staged_line = next(i for i, line in enumerate(lines) if "--staged" in line)
    exit_line = next(
        i for i, line in enumerate(lines) if line.strip() == 'exit "$status"'
    )
    exec_line = next(i for i, line in enumerate(lines) if line.startswith("exec"))
    assert staged_line < exit_line < exec_line


def test_hook_script_has_no_carriage_returns():
    """A CRLF hook fails under Git for Windows' sh (AGENTS.md / AGENT_NOTES.md)."""
    script = installer.render_hook_script(
        python_exe=Path("/venv/python"), preflight_script=Path("/repo/pre.py")
    )
    assert "\r" not in script


# --------------------------------------------------------------------- #
# --install gating and refusal                                           #
# --------------------------------------------------------------------- #


def test_install_without_yes_is_a_dry_run_that_writes_nothing(tmp_path, capsys):
    repo = _init_repo(tmp_path / "repo")
    _make_qualified_python(repo)
    code = installer.install(repo, yes=False)
    assert code == 0
    hook_path = installer.resolve_hook_directory(repo) / installer.HOOK_NAME
    assert not hook_path.exists()
    assert "Dry run" in capsys.readouterr().out


def test_install_with_yes_writes_the_wrapper(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    venv_python = _make_qualified_python(repo)
    code = installer.install(repo, yes=True, os_name="nt", access=lambda *a: True)
    assert code == 0
    hook_path = installer.resolve_hook_directory(repo) / installer.HOOK_NAME
    assert hook_path.is_file()
    content = hook_path.read_text(encoding="utf-8")
    assert installer.GENERATED_MARKER in content
    assert venv_python.as_posix() in content
    assert "\r" not in content


def test_install_refuses_to_overwrite_an_unknown_existing_hook(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _make_qualified_python(repo)
    hook_path = installer.resolve_hook_directory(repo) / installer.HOOK_NAME
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text("#!/bin/sh\necho hand-written\n", encoding="utf-8")

    code = installer.install(repo, yes=True, os_name="nt", access=lambda *a: True)
    assert code == 2
    assert hook_path.read_text(encoding="utf-8") == "#!/bin/sh\necho hand-written\n"


def test_install_is_idempotent_over_its_own_wrapper(tmp_path):
    """Installing twice over a wrapper this installer generated succeeds
    both times and produces byte-identical output, rather than refusing the
    second run as an "unknown" hook or drifting on repeated regeneration.
    """
    repo = _init_repo(tmp_path / "repo")
    _make_qualified_python(repo)

    first = installer.install(repo, yes=True, os_name="nt", access=lambda *a: True)
    hook_path = installer.resolve_hook_directory(repo) / installer.HOOK_NAME
    first_content = hook_path.read_text(encoding="utf-8")

    second = installer.install(repo, yes=True, os_name="nt", access=lambda *a: True)
    second_content = hook_path.read_text(encoding="utf-8")

    assert first == 0
    assert second == 0
    assert first_content == second_content


def test_install_fails_closed_when_interpreter_is_missing(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    # Deliberately do not create .venv/Scripts/python.exe.
    code = installer.install(repo, yes=True, os_name="nt", access=lambda *a: True)
    assert code == 2
    hook_path = installer.resolve_hook_directory(repo) / installer.HOOK_NAME
    assert not hook_path.exists()


def test_install_preserves_existing_graphify_hooks_beside_it(tmp_path):
    """Installing pre-commit must not disturb an unrelated hook file
    (post-commit, post-checkout) already present in the same directory --
    this repository's owner relies on exactly those for Graphify refresh.
    """
    repo = _init_repo(tmp_path / "repo")
    _make_qualified_python(repo)
    hook_dir = installer.resolve_hook_directory(repo)
    hook_dir.mkdir(parents=True, exist_ok=True)
    graphify_hook = hook_dir / "post-commit"
    graphify_hook.write_bytes(
        b"#!/bin/sh\npython scripts/dev/graphify_refresh.py --quiet || true\n"
    )

    code = installer.install(repo, yes=True, os_name="nt", access=lambda *a: True)
    assert code == 0
    assert graphify_hook.read_bytes() == (
        b"#!/bin/sh\npython scripts/dev/graphify_refresh.py --quiet || true\n"
    )


def test_install_never_touches_core_hooks_path(tmp_path):
    """Installing must not set or change core.hooksPath itself."""
    repo = _init_repo(tmp_path / "repo")
    _make_qualified_python(repo)
    assert installer.configured_hooks_path(repo) is None

    installer.install(repo, yes=True, os_name="nt", access=lambda *a: True)
    assert installer.configured_hooks_path(repo) is None


# --------------------------------------------------------------------- #
# Safe target containment                                                 #
# --------------------------------------------------------------------- #


def test_install_refuses_hooks_path_outside_repository_absolute(tmp_path, capsys):
    """An absolute core.hooksPath pointing entirely outside the repository
    (neither the worktree root nor the common Git directory) must be
    refused by --install -- writing a Git hook there is not this
    repository's decision to make silently.
    """
    repo = _init_repo(tmp_path / "repo")
    _make_qualified_python(repo)
    outside = tmp_path / "not-the-repo" / "hooks"
    _git(repo, "config", "core.hooksPath", str(outside))

    code = installer.install(repo, yes=True, os_name="nt", access=lambda *a: True)
    assert code == 2
    assert not (outside / installer.HOOK_NAME).exists()
    err_or_out = capsys.readouterr().out
    assert "outside this repository" in err_or_out


def test_install_refuses_hooks_path_dotdot_escape(tmp_path, capsys):
    """A relative core.hooksPath laced with '..' that resolves outside the
    worktree must be refused the same way an absolute escape is.
    """
    repo = _init_repo(tmp_path / "nested" / "repo")
    _make_qualified_python(repo)
    _git(repo, "config", "core.hooksPath", "../../escaped-hooks")

    code = installer.install(repo, yes=True, os_name="nt", access=lambda *a: True)
    assert code == 2
    escaped = (tmp_path / "escaped-hooks").resolve()
    assert not (escaped / installer.HOOK_NAME).exists()
    assert "outside this repository" in capsys.readouterr().out


def test_install_allows_hooks_path_inside_common_git_dir(tmp_path):
    """A hooksPath that stays inside the common .git directory (even if not
    the default hooks/ subdirectory) is a safe target, not an escape.
    """
    repo = _init_repo(tmp_path / "repo")
    _make_qualified_python(repo)
    common_dir = installer.git_common_dir(repo)
    custom = common_dir / "custom-hooks"
    _git(repo, "config", "core.hooksPath", str(custom))

    code = installer.install(repo, yes=True, os_name="nt", access=lambda *a: True)
    assert code == 0
    assert (custom / installer.HOOK_NAME).is_file()


def test_check_still_reports_an_outside_repository_target_without_refusing(tmp_path):
    """--check (inspect()) is read-only: it may still disclose an unsafe
    target so the operator can see it, without itself refusing anything --
    only --install enforces containment.
    """
    repo = _init_repo(tmp_path / "repo")
    outside = tmp_path / "not-the-repo" / "hooks"
    _git(repo, "config", "core.hooksPath", str(outside))

    disclosure = installer.inspect(repo)
    assert disclosure.hook_directory == outside


# --------------------------------------------------------------------- #
# Disclosure content (--check)                                           #
# --------------------------------------------------------------------- #


def test_check_discloses_every_affected_worktree(tmp_path, capsys):
    primary = _init_repo(tmp_path / "primary")
    linked = tmp_path / "linked"
    _git(primary, "worktree", "add", "-q", str(linked), "-b", "feature")

    disclosure = installer.inspect(primary)
    rendered = disclosure.render()
    assert str(primary.resolve()) in rendered
    assert str(linked.resolve()) in rendered
    assert len(disclosure.worktrees) == 2


def test_check_reports_absent_then_ours_after_install(tmp_path):
    repo = _init_repo(tmp_path / "repo")
    _make_qualified_python(repo)
    assert installer.inspect(repo).existing_status == "absent"
    installer.install(repo, yes=True, os_name="nt", access=lambda *a: True)
    assert installer.inspect(repo).existing_status == "ours"


def test_main_check_is_the_default_and_writes_nothing(tmp_path, monkeypatch, capsys):
    repo = _init_repo(tmp_path / "repo")
    _make_qualified_python(repo)
    monkeypatch.chdir(repo)
    assert installer.main([]) == 0
    hook_path = installer.resolve_hook_directory(repo) / installer.HOOK_NAME
    assert not hook_path.exists()
    assert "Resolved hook directory" in capsys.readouterr().out


# --------------------------------------------------------------------- #
# Real shell execution of the generated wrapper                          #
# --------------------------------------------------------------------- #

_SH = shutil.which("sh") or (
    r"C:\Program Files\Git\bin\sh.exe"
    if Path(r"C:\Program Files\Git\bin\sh.exe").is_file()
    else None
)


def _write_stub_python(tmp_path: Path, *, preflight_exit: int, marker: Path) -> Path:
    """Write a POSIX-sh stand-in for ``python_exe`` that understands only the
    two invocations the generated wrapper makes: ``<script> --staged`` (its
    first argument is a path, not ``-m``) and ``-m pre_commit hook-impl
    ...``. Git for Windows' ``sh`` honours the ``#!/bin/sh`` shebang on a
    direct invocation the same way a real POSIX shell would, so this stub
    can stand in for ``python`` without either the real docsync package or
    the real ``pre_commit`` package needing to be installed.
    """
    stub = tmp_path / "stub_python"
    stub.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "-m" ]; then\n'
        f'    : > "{marker.as_posix()}"\n'
        "    exit 0\n"
        "fi\n"
        f"exit {preflight_exit}\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return stub


@pytest.mark.skipif(_SH is None, reason="no POSIX sh available on this host")
def test_generated_wrapper_blocks_delegation_on_preflight_failure(tmp_path):
    """Real end-to-end proof: when the preflight step exits nonzero, the
    stand-in for ``pre_commit hook-impl`` is never reached at all.
    """
    marker = tmp_path / "hook_impl_ran.txt"
    stub_python = _write_stub_python(tmp_path, preflight_exit=5, marker=marker)
    preflight_script = tmp_path / "preflight.py"
    preflight_script.write_text("# unused by the stub\n", encoding="utf-8")

    hook_path = tmp_path / "pre-commit"
    hook_path.write_bytes(
        installer.render_hook_script(
            python_exe=stub_python, preflight_script=preflight_script
        ).encode("utf-8")
    )

    result = subprocess.run(
        [_SH, str(hook_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 5
    assert not marker.exists()


@pytest.mark.skipif(_SH is None, reason="no POSIX sh available on this host")
def test_generated_wrapper_delegates_on_preflight_success(tmp_path):
    """Real end-to-end proof: a passing preflight reaches the delegate call."""
    marker = tmp_path / "hook_impl_ran.txt"
    stub_python = _write_stub_python(tmp_path, preflight_exit=0, marker=marker)
    preflight_script = tmp_path / "preflight.py"
    preflight_script.write_text("# unused by the stub\n", encoding="utf-8")

    hook_path = tmp_path / "pre-commit"
    hook_path.write_bytes(
        installer.render_hook_script(
            python_exe=stub_python, preflight_script=preflight_script
        ).encode("utf-8")
    )

    result = subprocess.run(
        [_SH, str(hook_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert marker.exists()
    assert result.returncode == 0


# --------------------------------------------------------------------- #
# SKIP=doc-state-sync-check (owner ruling: the one supported local escape) #
# --------------------------------------------------------------------- #


def test_hook_script_checks_skip_for_the_hook_id():
    """Content-level: the rendered script tests SKIP for this hook's own id."""
    script = installer.render_hook_script(
        python_exe=Path("/venv/python"), preflight_script=Path("/repo/pre.py")
    )
    assert "$SKIP" in script
    assert "doc-state-sync-check" in script


@pytest.mark.skipif(_SH is None, reason="no POSIX sh available on this host")
def test_generated_wrapper_skips_preflight_when_skip_names_the_hook(tmp_path):
    """Real end-to-end proof of the owner ruling's one supported local
    escape: SKIP=doc-state-sync-check reaches the delegate call even though
    the preflight step, if it ran, would fail (nonzero exit) -- proving the
    preflight step was genuinely skipped, not merely successful.
    """
    marker = tmp_path / "hook_impl_ran.txt"
    stub_python = _write_stub_python(tmp_path, preflight_exit=9, marker=marker)
    preflight_script = tmp_path / "preflight.py"
    preflight_script.write_text("# unused by the stub\n", encoding="utf-8")

    hook_path = tmp_path / "pre-commit"
    hook_path.write_bytes(
        installer.render_hook_script(
            python_exe=stub_python, preflight_script=preflight_script
        ).encode("utf-8")
    )

    env = dict(**_env_without_skip(), SKIP="doc-state-sync-check")
    result = subprocess.run(
        [_SH, str(hook_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert marker.exists()
    assert result.returncode == 0


@pytest.mark.skipif(_SH is None, reason="no POSIX sh available on this host")
def test_generated_wrapper_skip_matches_within_a_comma_separated_list(tmp_path):
    """pre-commit's own SKIP is comma-separated; this hook's id must match
    as one entry among several, not just when it is the only value.
    """
    marker = tmp_path / "hook_impl_ran.txt"
    stub_python = _write_stub_python(tmp_path, preflight_exit=9, marker=marker)
    preflight_script = tmp_path / "preflight.py"
    preflight_script.write_text("# unused by the stub\n", encoding="utf-8")

    hook_path = tmp_path / "pre-commit"
    hook_path.write_bytes(
        installer.render_hook_script(
            python_exe=stub_python, preflight_script=preflight_script
        ).encode("utf-8")
    )

    env = dict(
        **_env_without_skip(), SKIP="some-other-hook,doc-state-sync-check,another"
    )
    result = subprocess.run(
        [_SH, str(hook_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert marker.exists()
    assert result.returncode == 0


@pytest.mark.skipif(_SH is None, reason="no POSIX sh available on this host")
def test_generated_wrapper_does_not_skip_for_unrelated_skip_value(tmp_path):
    """A SKIP value that merely contains this hook's id as a substring of a
    different name (not a full comma-delimited match) must not skip it --
    proof the match is exact, not a loose substring test.
    """
    marker = tmp_path / "hook_impl_ran.txt"
    stub_python = _write_stub_python(tmp_path, preflight_exit=9, marker=marker)
    preflight_script = tmp_path / "preflight.py"
    preflight_script.write_text("# unused by the stub\n", encoding="utf-8")

    hook_path = tmp_path / "pre-commit"
    hook_path.write_bytes(
        installer.render_hook_script(
            python_exe=stub_python, preflight_script=preflight_script
        ).encode("utf-8")
    )

    env = dict(**_env_without_skip(), SKIP="doc-state-sync-check-other")
    result = subprocess.run(
        [_SH, str(hook_path)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert not marker.exists()
    assert result.returncode == 9


def _env_without_skip() -> dict:
    """This process's environment, minus any inherited SKIP value.

    Isolates the SKIP-specific tests above from whatever the host shell
    that launched the test session happens to have set.
    """
    import os

    return {key: value for key, value in os.environ.items() if key != "SKIP"}
