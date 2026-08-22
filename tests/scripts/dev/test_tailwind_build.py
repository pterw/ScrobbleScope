"""Tests for pinned Tailwind and daisyUI artifact management."""

from __future__ import annotations

import hashlib
import http.client
import platform
import stat
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

import pytest

from scripts.dev.tailwind_build import (
    DAISYUI_ARTIFACTS,
    TAILWIND_ARTIFACTS,
    ArtifactSpec,
    TailwindBuildError,
    _detect_libc,
    _download_verified,
    _mark_executable,
    ensure_artifact,
    ensure_toolchain,
    platform_key,
    required_artifacts,
    sha256_file,
)


def _artifact(payload: bytes = b"trusted", *, executable: bool = False) -> ArtifactSpec:
    """Create a self-consistent local artifact specification for tests."""
    return ArtifactSpec(
        filename="asset.bin",
        url="https://example.invalid/asset.bin",
        sha256=hashlib.sha256(payload).hexdigest(),
        executable=executable,
    )


@pytest.mark.parametrize(
    ("system", "machine", "libc", "expected"),
    [
        ("Windows", "AMD64", "", "windows-x64"),
        ("Darwin", "x86_64", "", "macos-x64"),
        ("Darwin", "arm64", "", "macos-arm64"),
        ("Linux", "x86_64", "glibc", "linux-x64"),
        ("Linux", "x86_64", "libc", "linux-x64"),
        ("Linux", "AMD64", "musl", "linux-x64-musl"),
        ("Linux", "aarch64", "glibc", "linux-arm64"),
        ("Linux", "arm64", "musl", "linux-arm64-musl"),
    ],
)
def test_platform_key_maps_every_official_asset(
    system: str,
    machine: str,
    libc: str,
    expected: str,
) -> None:
    """Every official host maps to exactly one pinned Tailwind artifact."""
    assert platform_key(system=system, machine=machine, libc=libc) == expected


@pytest.mark.parametrize(
    ("system", "machine", "libc", "expected_key"),
    [
        ("Windows", "AMD64", "", "windows-x64"),
        ("Darwin", "x86_64", "", "macos-x64"),
        ("Darwin", "arm64", "", "macos-arm64"),
        ("Linux", "x86_64", "glibc", "linux-x64"),
        ("Linux", "x86_64", "libc", "linux-x64"),
        ("Linux", "AMD64", "musl", "linux-x64-musl"),
        ("Linux", "aarch64", "glibc", "linux-arm64"),
        ("Linux", "arm64", "musl", "linux-arm64-musl"),
    ],
)
def test_required_artifacts_selects_host_then_plugins(
    system: str,
    machine: str,
    libc: str,
    expected_key: str,
) -> None:
    """Every explicit host selects its executable before both plugin bundles."""
    assert required_artifacts(system=system, machine=machine, libc=libc) == (
        TAILWIND_ARTIFACTS[expected_key],
        *DAISYUI_ARTIFACTS,
    )


@pytest.mark.parametrize(
    ("system", "machine", "libc"),
    [
        ("Windows", "arm64", ""),
        ("Linux", "i686", "glibc"),
        ("Linux", "x86_64", "unknown"),
        ("FreeBSD", "x86_64", ""),
    ],
)
def test_platform_key_fails_closed_for_an_unsupported_host(
    system: str,
    machine: str,
    libc: str,
) -> None:
    """An unknown host must not guess at an executable."""
    with pytest.raises(TailwindBuildError, match="Unsupported Tailwind platform"):
        platform_key(system=system, machine=machine, libc=libc)


@pytest.mark.parametrize(
    ("system", "machine", "libc", "expected_detail"),
    [
        ("", "x86_64", "glibc", "system=''"),
        ("Linux", "", "glibc", "machine=''"),
    ],
)
def test_platform_key_fails_closed_for_explicit_empty_host_values(
    system: str,
    machine: str,
    libc: str,
    expected_detail: str,
) -> None:
    """Explicit empty host values must not probe or guess from the live host."""
    with pytest.raises(
        TailwindBuildError, match="Unsupported Tailwind platform"
    ) as exc:
        platform_key(system=system, machine=machine, libc=libc)

    assert expected_detail in str(exc.value)


@pytest.mark.parametrize(
    ("loader_names", "expected"),
    [
        (("ld-musl-x86_64.so.1",), "musl"),
        (("ld-musl-aarch64.so.1",), "musl"),
        ((), ""),
        (("ld-linux-x86-64.so.2",), ""),
    ],
)
def test_detect_libc_reads_the_musl_loader_when_python_reports_nothing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    loader_names: tuple[str, ...],
    expected: str,
) -> None:
    """musl hosts report no libc version, so its loader is the only signal."""
    monkeypatch.setattr(platform, "libc_ver", lambda *_a, **_k: ("", ""))
    for name in loader_names:
        (tmp_path / name).touch()

    assert _detect_libc(lib_dir=tmp_path) == expected


def test_detect_libc_prefers_the_reported_runtime_over_the_loader_probe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A reported runtime is authoritative; the loader probe is a fallback."""
    monkeypatch.setattr(platform, "libc_ver", lambda *_a, **_k: ("glibc", "2.41"))
    (tmp_path / "ld-musl-x86_64.so.1").touch()

    assert _detect_libc(lib_dir=tmp_path) == "glibc"


def test_release_catalog_pins_the_reviewed_versions_and_digests() -> None:
    """Security pins name every executable and both required plugin bundles."""
    expected_tailwind = {
        "linux-arm64": "55fd0b241214eff3de1e8ee4f22796662f2d2e7a49bcfca7477cfd0bac398195",
        "linux-arm64-musl": "71ea4be79c9de9827545682df3e040053fb535d37c71ed2cfdedf9385a0868e0",
        "linux-x64": "dc61b3ac6b8c9ca874c0cc4c57b2409791a64c5540404ca5f5367360babc313a",
        "linux-x64-musl": "a04d34ceacc8f52cbe8920ad846cdeb61d3d0021dba32db0d1f77c9d9fad7a6c",
        "macos-arm64": "cdf646702987a743464dff4d9c60fd4480d1c1e73dd819a9a67f1078815dce9d",
        "macos-x64": "7922e0953f2110c05976e3bf58f14e643d90427575e766b7d433f5f80cbee7e1",
        "windows-x64": "e0e260ce048014e9268f6237ff18f8ccf02cef521cbd0ae04e82c2cdf7aa3955",
    }
    expected_daisyui = {
        "daisyui.mjs": "21d1e62434bfccf64b67d3eee3958194ce75c9251180c77a86cc6ad5abef8df8",
        "daisyui-theme.mjs": "a097897fb2d46329483f9ec452583407369317d732c8b23efbdff3f8391c4b82",
    }

    assert {key: spec.sha256 for key, spec in TAILWIND_ARTIFACTS.items()} == (
        expected_tailwind
    )
    assert {spec.filename: spec.sha256 for spec in DAISYUI_ARTIFACTS} == (
        expected_daisyui
    )
    assert all("/v4.3.3/" in spec.url for spec in TAILWIND_ARTIFACTS.values())
    assert all("/v5.7.19/" in spec.url for spec in DAISYUI_ARTIFACTS)
    assert all("/latest/" not in spec.url for spec in required_artifacts())


def test_a_valid_cached_artifact_is_rehashed_without_network(tmp_path: Path) -> None:
    """A persistent cache is trusted only after a fresh digest on each use."""
    spec = _artifact()
    destination = tmp_path / spec.filename
    destination.write_bytes(b"trusted")

    with (
        patch(
            "scripts.dev.tailwind_build.urlopen",
            side_effect=AssertionError("network must not be used"),
        ),
        patch(
            "scripts.dev.tailwind_build.sha256_file",
            wraps=sha256_file,
        ) as digest,
    ):
        assert ensure_artifact(spec, bin_dir=tmp_path) == destination
        assert ensure_artifact(spec, bin_dir=tmp_path) == destination

    assert digest.call_count == 2


class _StubResponse:
    """Minimal urlopen stand-in: a context manager exposing headers and read.

    A real HTTPResponse always carries headers. io.BytesIO does not, so a
    stub without them cannot exercise the Content-Length short-read check.
    """

    def __init__(self, headers: dict[str, str], reader) -> None:
        self.headers = headers
        self._reader = reader

    def read(self, size: int) -> bytes:
        return self._reader(size)

    def __enter__(self) -> "_StubResponse":
        return self

    def __exit__(self, *_exc_info: object) -> bool:
        return False


def _response(payload: bytes, *, declared: int | None = None) -> _StubResponse:
    """Serve payload in one read, then end-of-body, with a Content-Length."""
    remaining = [payload]
    length = len(payload) if declared is None else declared
    return _StubResponse(
        {"Content-Length": str(length)},
        lambda _size: remaining.pop(0) if remaining else b"",
    )


def test_a_missing_artifact_is_downloaded_and_verified(tmp_path: Path) -> None:
    """A cache miss publishes exactly the bytes covered by the pinned digest."""
    spec = _artifact()

    with patch(
        "scripts.dev.tailwind_build.urlopen",
        return_value=_response(b"trusted"),
    ) as opener:
        destination = ensure_artifact(spec, bin_dir=tmp_path)

    assert destination.read_bytes() == b"trusted"
    assert opener.call_count == 1
    assert opener.call_args.kwargs["timeout"] == 60


def test_a_corrupt_cache_entry_is_replaced_once(tmp_path: Path) -> None:
    """A bad persistent file triggers one verified replacement download."""
    spec = _artifact()
    destination = tmp_path / spec.filename
    destination.write_bytes(b"tampered")

    with patch(
        "scripts.dev.tailwind_build.urlopen",
        return_value=_response(b"trusted"),
    ) as opener:
        assert ensure_artifact(spec, bin_dir=tmp_path) == destination

    assert opener.call_count == 1
    assert destination.read_bytes() == b"trusted"


def test_a_corrupt_replacement_fails_closed_and_cleans_temp_file(
    tmp_path: Path,
) -> None:
    """Untrusted replacement bytes never overwrite the previous cache entry."""
    spec = _artifact()
    destination = tmp_path / spec.filename
    destination.write_bytes(b"tampered")

    with (
        patch(
            "scripts.dev.tailwind_build.urlopen",
            return_value=_response(b"also-wrong"),
        ) as opener,
        pytest.raises(TailwindBuildError, match="SHA-256 mismatch"),
    ):
        ensure_artifact(spec, bin_dir=tmp_path)

    assert opener.call_count == 1
    assert destination.read_bytes() == b"tampered"
    assert [path for path in tmp_path.iterdir() if path.suffix == ".tmp"] == []


def test_a_download_error_cleans_the_temporary_file(tmp_path: Path) -> None:
    """A failed fetch leaves neither executable bytes nor a partial download."""
    spec = _artifact()

    with (
        patch(
            "scripts.dev.tailwind_build.urlopen",
            side_effect=URLError("offline"),
        ),
        pytest.raises(TailwindBuildError, match="Could not fetch"),
    ):
        ensure_artifact(spec, bin_dir=tmp_path)

    assert list(tmp_path.iterdir()) == []


def test_a_truncated_download_is_reported_as_a_short_read(tmp_path: Path) -> None:
    """A connection that closes mid-body must not be blamed on the digest.

    A short file fails the digest check for a network reason. Reporting that
    as "SHA-256 mismatch" reads as a supply-chain compromise and sends the
    operator to investigate the wrong thing.
    """
    payload = b"the full body"
    spec = _artifact(payload)
    response = _StubResponse({"Content-Length": str(len(payload))}, lambda _size: b"")

    with (
        patch("scripts.dev.tailwind_build.urlopen", return_value=response),
        pytest.raises(TailwindBuildError) as error,
    ):
        _download_verified(spec, tmp_path / spec.filename)

    message = str(error.value)
    assert "truncated" in message.lower()
    assert "SHA-256 mismatch" not in message
    assert str(len(payload)) in message


def test_an_incomplete_read_is_translated_not_raised_raw(tmp_path: Path) -> None:
    """IncompleteRead subclasses HTTPException, so it escapes an OSError catch."""

    def _raise(_size: int) -> bytes:
        raise http.client.IncompleteRead(b"partial", 6)

    spec = _artifact(b"the full body")
    response = _StubResponse({}, _raise)

    with (
        patch("scripts.dev.tailwind_build.urlopen", return_value=response),
        pytest.raises(TailwindBuildError, match="Could not fetch"),
    ):
        _download_verified(spec, tmp_path / spec.filename)

    assert [path for path in tmp_path.iterdir() if path.suffix == ".tmp"] == []


def test_ensure_toolchain_checks_the_executable_and_both_bundles(
    tmp_path: Path,
) -> None:
    """One build cannot skip integrity verification for either daisyUI file."""
    specs = (
        _artifact(b"tailwind", executable=True),
        ArtifactSpec(
            "daisyui.mjs",
            "https://example.invalid/daisyui.mjs",
            hashlib.sha256(b"components").hexdigest(),
        ),
        ArtifactSpec(
            "daisyui-theme.mjs",
            "https://example.invalid/daisyui-theme.mjs",
            hashlib.sha256(b"themes").hexdigest(),
        ),
    )

    with (
        patch("scripts.dev.tailwind_build.required_artifacts", return_value=specs),
        patch("scripts.dev.tailwind_build.ensure_artifact") as ensure,
    ):
        ensure.side_effect = [tmp_path / spec.filename for spec in specs]
        executable = ensure_toolchain(bin_dir=tmp_path)

    assert executable == tmp_path / "asset.bin"
    assert [call.args[0] for call in ensure.call_args_list] == list(specs)
    # Reading args alone leaves bin_dir unchecked, so dropping the keyword in
    # ensure_toolchain kept the whole suite green. Assert the routing too.
    assert [call.kwargs["bin_dir"] for call in ensure.call_args_list] == [tmp_path] * 3


def test_executable_mode_is_added_only_on_posix(tmp_path: Path) -> None:
    """Linux and macOS assets become executable while Windows remains untouched."""
    path = tmp_path / "tailwindcss"
    path.write_bytes(b"trusted")
    original_mode = path.stat().st_mode

    with patch.object(Path, "chmod") as windows_chmod:
        _mark_executable(path, os_name="nt")

    windows_chmod.assert_not_called()

    with patch.object(Path, "chmod") as posix_chmod:
        _mark_executable(path, os_name="posix")

    posix_chmod.assert_called_once_with(
        original_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )
