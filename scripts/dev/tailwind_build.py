#!/usr/bin/env python3
"""Build committed Tailwind CSS with pinned, verified standalone assets."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import stat
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = REPO_ROOT / "scripts" / "bin"
SOURCE_CSS = REPO_ROOT / "static" / "css" / "tailwind.src.css"
OUTPUT_CSS = REPO_ROOT / "static" / "css" / "tailwind.css"

TAILWIND_VERSION = "v4.3.3"
DAISYUI_VERSION = "v5.7.19"
DOWNLOAD_TIMEOUT_SECONDS = 60
DOWNLOAD_CHUNK_SIZE = 1024 * 1024


class TailwindBuildError(RuntimeError):
    """Report a safe, actionable toolchain or build failure."""


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    """Describe one pinned release asset and its trusted digest."""

    filename: str
    url: str
    sha256: str
    executable: bool = False


def _tailwind_artifact(asset_name: str, sha256: str) -> ArtifactSpec:
    """Build one immutable Tailwind release specification."""
    return ArtifactSpec(
        filename=asset_name,
        url=(
            "https://github.com/tailwindlabs/tailwindcss/releases/download/"
            f"{TAILWIND_VERSION}/{asset_name}"
        ),
        sha256=sha256,
        executable=True,
    )


def _daisyui_artifact(filename: str, sha256: str) -> ArtifactSpec:
    """Build one immutable daisyUI bundle specification."""
    return ArtifactSpec(
        filename=filename,
        url=(
            "https://github.com/saadeghi/daisyui/releases/download/"
            f"{DAISYUI_VERSION}/{filename}"
        ),
        sha256=sha256,
    )


TAILWIND_ARTIFACTS = {
    "linux-arm64": _tailwind_artifact(
        "tailwindcss-linux-arm64",
        "55fd0b241214eff3de1e8ee4f22796662f2d2e7a49bcfca7477cfd0bac398195",
    ),
    "linux-arm64-musl": _tailwind_artifact(
        "tailwindcss-linux-arm64-musl",
        "71ea4be79c9de9827545682df3e040053fb535d37c71ed2cfdedf9385a0868e0",
    ),
    "linux-x64": _tailwind_artifact(
        "tailwindcss-linux-x64",
        "dc61b3ac6b8c9ca874c0cc4c57b2409791a64c5540404ca5f5367360babc313a",
    ),
    "linux-x64-musl": _tailwind_artifact(
        "tailwindcss-linux-x64-musl",
        "a04d34ceacc8f52cbe8920ad846cdeb61d3d0021dba32db0d1f77c9d9fad7a6c",
    ),
    "macos-arm64": _tailwind_artifact(
        "tailwindcss-macos-arm64",
        "cdf646702987a743464dff4d9c60fd4480d1c1e73dd819a9a67f1078815dce9d",
    ),
    "macos-x64": _tailwind_artifact(
        "tailwindcss-macos-x64",
        "7922e0953f2110c05976e3bf58f14e643d90427575e766b7d433f5f80cbee7e1",
    ),
    "windows-x64": _tailwind_artifact(
        "tailwindcss-windows-x64.exe",
        "e0e260ce048014e9268f6237ff18f8ccf02cef521cbd0ae04e82c2cdf7aa3955",
    ),
}

DAISYUI_ARTIFACTS = (
    _daisyui_artifact(
        "daisyui.mjs",
        "21d1e62434bfccf64b67d3eee3958194ce75c9251180c77a86cc6ad5abef8df8",
    ),
    _daisyui_artifact(
        "daisyui-theme.mjs",
        "a097897fb2d46329483f9ec452583407369317d732c8b23efbdff3f8391c4b82",
    ),
)


def _normalize_libc(name: str) -> str:
    """Map a reported C runtime name onto Tailwind's asset vocabulary.

    `platform.libc_ver()` reports `glibc` from its `confstr` path and `libc`
    from its ELF fallback. Both name the same GNU runtime.
    """
    lowered = name.casefold()
    return "glibc" if lowered in {"glibc", "libc"} else lowered


def _detect_libc(*, lib_dir: Path | None = None) -> str:
    """Name the C runtime of the running Linux host.

    `platform.libc_ver()` reports nothing at all on musl, so the musl dynamic
    loader is the only positive signal available without running a
    subprocess. An explicit `lib_dir` keeps that probe deterministic in tests.
    """
    reported = platform.libc_ver()[0]
    if reported:
        return reported
    loader_dir = lib_dir if lib_dir is not None else Path("/lib")
    if any(loader_dir.glob("ld-musl-*.so.1")):
        return "musl"
    return ""


def platform_key(
    *,
    system: str | None = None,
    machine: str | None = None,
    libc: str | None = None,
) -> str:
    """Return the official Tailwind asset key for one supported host.

    Explicit values make the platform matrix deterministic in tests. Omitted
    values come from the running Python process. Linux distinguishes musl from
    glibc and fails closed when neither runtime can be identified.
    """
    system_value = system if system is not None else platform.system()
    machine_value = machine if machine is not None else platform.machine()
    system_name = system_value.casefold()
    machine_name = machine_value.casefold()
    architecture = {
        "amd64": "x64",
        "x86_64": "x64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }.get(machine_name)

    if system_name == "windows" and architecture == "x64":
        key = "windows-x64"
    elif system_name == "darwin" and architecture in {"x64", "arm64"}:
        key = f"macos-{architecture}"
    elif system_name == "linux" and architecture in {"x64", "arm64"}:
        libc_value = libc if libc is not None else _detect_libc()
        libc_name = _normalize_libc(libc_value)
        if libc_name not in {"glibc", "musl"}:
            raise TailwindBuildError(
                "Unsupported Tailwind platform: "
                f"system={system_value!r}, "
                f"machine={machine_value!r}, "
                f"libc={libc_value!r}"
            )
        suffix = "-musl" if libc_name == "musl" else ""
        key = f"linux-{architecture}{suffix}"
    else:
        raise TailwindBuildError(
            "Unsupported Tailwind platform: "
            f"system={system_value!r}, "
            f"machine={machine_value!r}"
        )

    return key


def required_artifacts(
    *,
    system: str | None = None,
    machine: str | None = None,
    libc: str | None = None,
) -> tuple[ArtifactSpec, ...]:
    """Return the host executable followed by both required daisyUI bundles."""
    tailwind = TAILWIND_ARTIFACTS[
        platform_key(system=system, machine=machine, libc=libc)
    ]
    return (tailwind, *DAISYUI_ARTIFACTS)


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest of one file's exact bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(DOWNLOAD_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _mark_executable(path: Path, *, os_name: str | None = None) -> None:
    """Add executable bits for Unix hosts without changing Windows mode."""
    if (os_name or os.name) == "nt":
        return
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _download_verified(spec: ArtifactSpec, destination: Path) -> None:
    """Download, verify, and atomically publish one pinned release asset.

    The destination is never replaced until the complete temporary file has
    the trusted digest. All error paths delete the temporary file. A caller
    invokes this once per missing or invalid cache entry, which implements the
    one-refetch rule.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    request = Request(spec.url, headers={"User-Agent": "ScrobbleScope-tailwind-build"})

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{spec.filename}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            try:
                with urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                    while chunk := response.read(DOWNLOAD_CHUNK_SIZE):
                        temporary.write(chunk)
            except (OSError, URLError) as exc:
                raise TailwindBuildError(
                    f"Could not fetch pinned artifact {spec.filename}: {exc}"
                ) from exc

        actual = sha256_file(temporary_path)
        if actual != spec.sha256:
            raise TailwindBuildError(
                f"SHA-256 mismatch for {spec.filename}: "
                f"expected {spec.sha256}, got {actual}"
            )

        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def ensure_artifact(
    spec: ArtifactSpec,
    *,
    bin_dir: Path = BIN_DIR,
) -> Path:
    """Return one verified cached artifact, refetching once when necessary."""
    destination = bin_dir / spec.filename
    if destination.is_file() and sha256_file(destination) == spec.sha256:
        if spec.executable:
            _mark_executable(destination)
        return destination

    print(f"[tailwind_build] fetching {spec.filename}")
    _download_verified(spec, destination)
    if sha256_file(destination) != spec.sha256:
        raise TailwindBuildError(
            f"Cached artifact failed verification after fetch: {spec.filename}"
        )
    if spec.executable:
        _mark_executable(destination)
    return destination


def ensure_toolchain(
    *,
    bin_dir: Path = BIN_DIR,
    system: str | None = None,
    machine: str | None = None,
    libc: str | None = None,
) -> Path:
    """Verify all required artifacts and return the host Tailwind executable."""
    specs = required_artifacts(system=system, machine=machine, libc=libc)
    paths = tuple(ensure_artifact(spec, bin_dir=bin_dir) for spec in specs)
    return paths[0]


def build_tailwind(*, watch: bool = False) -> None:
    """Verify the toolchain and compile the committed Tailwind stylesheet."""
    executable = ensure_toolchain()
    command = [
        str(executable),
        "-i",
        str(SOURCE_CSS),
        "-o",
        str(OUTPUT_CSS),
    ]
    if watch:
        command.append("--watch")

    print(
        "[tailwind_build] "
        f"building {OUTPUT_CSS.relative_to(REPO_ROOT)}"
        + (" in watch mode" if watch else "")
    )
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the single supported developer-facing build option."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--watch",
        action="store_true",
        help="rebuild static/css/tailwind.css whenever source content changes",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Tailwind build and translate expected failures to exit code 1."""
    args = _parse_args(argv)
    try:
        build_tailwind(watch=args.watch)
    except (TailwindBuildError, subprocess.CalledProcessError, OSError) as exc:
        print(f"[tailwind_build] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
