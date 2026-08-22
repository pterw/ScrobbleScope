"""Tests for the Tailwind build CLI and CSS source contract."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from scripts.dev.tailwind_build import (
    OUTPUT_CSS,
    REPO_ROOT,
    SOURCE_CSS,
    TailwindBuildError,
    build_tailwind,
    main,
)


def test_one_shot_build_uses_the_verified_executable_and_fixed_paths() -> None:
    """The guaranteed rebuild path is independent of the caller's directory."""
    executable = REPO_ROOT / "scripts" / "bin" / "tailwindcss-test"

    with (
        patch(
            "scripts.dev.tailwind_build.ensure_toolchain",
            return_value=executable,
        ),
        patch("scripts.dev.tailwind_build.subprocess.run") as run,
    ):
        build_tailwind()

    run.assert_called_once_with(
        [str(executable), "-i", str(SOURCE_CSS), "-o", str(OUTPUT_CSS)],
        cwd=REPO_ROOT,
        check=True,
    )


def test_watch_build_adds_only_the_watch_flag() -> None:
    """Watch mode keeps the same source, destination, and verified toolchain."""
    executable = REPO_ROOT / "scripts" / "bin" / "tailwindcss-test"

    with (
        patch(
            "scripts.dev.tailwind_build.ensure_toolchain",
            return_value=executable,
        ),
        patch("scripts.dev.tailwind_build.subprocess.run") as run,
    ):
        build_tailwind(watch=True)

    run.assert_called_once_with(
        [
            str(executable),
            "-i",
            str(SOURCE_CSS),
            "-o",
            str(OUTPUT_CSS),
            "--watch",
        ],
        cwd=REPO_ROOT,
        check=True,
    )


def test_main_passes_watch_to_the_build() -> None:
    """The public CLI exposes one optional switch and no alternate build path."""
    with patch("scripts.dev.tailwind_build.build_tailwind") as build:
        assert main(["--watch"]) == 0

    build.assert_called_once_with(watch=True)


def test_main_reports_a_safe_failure(capsys) -> None:
    """Toolchain failures return nonzero without a traceback or silent success."""
    with patch(
        "scripts.dev.tailwind_build.build_tailwind",
        side_effect=TailwindBuildError("digest rejected"),
    ):
        assert main([]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "[tailwind_build] ERROR: digest rejected\n"


def test_main_reports_a_failed_tailwind_process(capsys) -> None:
    """A nonzero standalone CLI exit is visible to local and CI callers."""
    failure = subprocess.CalledProcessError(2, ["tailwindcss"])
    with patch(
        "scripts.dev.tailwind_build.build_tailwind",
        side_effect=failure,
    ):
        assert main([]) == 1

    assert "returned non-zero exit status 2" in capsys.readouterr().err


def test_theme_source_locks_the_batch_21_design_tokens() -> None:
    """The source owns exact palette, type, spacing, radius, and bar aliases."""
    source = SOURCE_CSS.read_text(encoding="utf-8")
    required_lines = {
        '--font-sans: "akzidenz-grotesk-next-pro", ui-sans-serif, system-ui, sans-serif;',
        '--font-serif: "instrument-serif", Georgia, serif;',
        '--font-figure: "gotham", ui-sans-serif, sans-serif;',
        '--font-mono: "input-mono", ui-monospace, monospace;',
        '--font-mono-narrow: "input-mono-narrow", "input-mono", ui-monospace, monospace;',
        "--text-label-sm: 0.71875rem;",
        "--text-label: 0.8125rem;",
        "--text-body-sm: 0.875rem;",
        "--text-body: 1rem;",
        "--text-display: 1.5rem;",
        "--spacing-1: 0.25rem;",
        "--spacing-2: 0.5rem;",
        "--spacing-3: 0.75rem;",
        "--spacing-4: 1rem;",
        "--spacing-6: 1.5rem;",
        "--spacing-8: 2rem;",
        "--spacing-12: 3rem;",
        "--radius-sm: 8px;",
        "--radius-lg: 14px;",
        "--radius-full: 999px;",
    }
    actual_lines = {line.strip() for line in source.splitlines()}

    assert required_lines <= actual_lines
    for color in (
        "#faf8f3",
        "#f0ebe0",
        "#1a1820",
        "#6a4baf",
        "#0e0c12",
        "#181520",
        "#f1ede4",
        "#b39dde",
    ):
        assert color in source
    assert source.count("--bars-color: var(--color-primary);") == 2
    assert "#f8f9fa" not in source
    assert "#121212" not in source
    # Adobe Fonts kit rwy8ghw serves 300/400/700 only. A 500 or 600 token
    # cannot resolve to a real face, so the browser synthesizes a fake one.
    assert "--font-weight-medium" not in source
    assert "--font-weight-semibold" not in source


def test_theme_source_includes_only_the_locked_daisyui_components() -> None:
    """Class discovery in bundle files cannot silently enable all components."""
    source = SOURCE_CSS.read_text(encoding="utf-8")
    include_line = next(
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith("include:")
    )
    components = {
        component.strip()
        for component in include_line.removeprefix("include:")
        .removesuffix(";")
        .split(",")
    }

    assert components == {
        "button",
        "card",
        "modal",
        "toggle",
        "input",
        "select",
        "tab",
        "toast",
        "alert",
    }
    assert '@source not "../../scripts/bin/*";' in source
    assert '@plugin "../../scripts/bin/daisyui-theme.mjs" {' in source
