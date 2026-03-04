"""Unit tests for scripts.dev.dev_start.

All tests mock subprocess.run so Docker is never invoked.  Each test exercises
a distinct error path or success branch in check_container_status, start_container,
or main.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from scripts.dev.dev_start import check_container_status, main, start_container

# ---------------------------------------------------------------------------
# check_container_status
# ---------------------------------------------------------------------------


def test_check_container_status_returns_running():
    """GIVEN docker inspect exits 0 with 'running'
    WHEN check_container_status is called
    THEN it returns 'running'.
    """
    mock_result = MagicMock(returncode=0, stdout="running\n", stderr="")
    with patch("scripts.dev.dev_start.subprocess.run", return_value=mock_result):
        assert check_container_status("ss-postgres") == "running"


def test_check_container_status_returns_none_for_absent_container():
    """GIVEN docker inspect exits non-zero with 'No such object' in stderr
    WHEN check_container_status is called
    THEN it returns None (container does not exist).
    """
    mock_result = MagicMock(
        returncode=1,
        stdout="",
        stderr="Error: No such object: ss-postgres\n",
    )
    with patch("scripts.dev.dev_start.subprocess.run", return_value=mock_result):
        assert check_container_status("ss-postgres") is None


def test_check_container_status_raises_when_docker_not_found():
    """GIVEN subprocess.run raises FileNotFoundError (docker not on PATH)
    WHEN check_container_status is called
    THEN it raises RuntimeError mentioning 'docker executable'.
    """
    with patch(
        "scripts.dev.dev_start.subprocess.run",
        side_effect=FileNotFoundError,
    ):
        with pytest.raises(RuntimeError, match="docker executable not found"):
            check_container_status("ss-postgres")


def test_check_container_status_raises_on_timeout():
    """GIVEN docker inspect times out (hung daemon)
    WHEN check_container_status is called
    THEN it raises RuntimeError mentioning 'timed out'.
    """
    with patch(
        "scripts.dev.dev_start.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=10),
    ):
        with pytest.raises(RuntimeError, match="timed out"):
            check_container_status("ss-postgres")


def test_check_container_status_raises_when_daemon_not_running():
    """GIVEN docker inspect exits non-zero with 'Cannot connect to the Docker daemon'
    WHEN check_container_status is called
    THEN it raises RuntimeError about daemon not reachable.
    """
    mock_result = MagicMock(
        returncode=1,
        stdout="",
        stderr="Cannot connect to the Docker daemon at unix:///var/run/docker.sock",
    )
    with patch("scripts.dev.dev_start.subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Docker daemon is not reachable"):
            check_container_status("ss-postgres")


def test_check_container_status_raises_on_unexpected_error():
    """GIVEN docker inspect exits non-zero with an unrecognized error
    WHEN check_container_status is called
    THEN it raises RuntimeError with the stderr details.
    """
    mock_result = MagicMock(
        returncode=1,
        stdout="",
        stderr="Some unexpected docker error\n",
    )
    with patch("scripts.dev.dev_start.subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Unexpected error"):
            check_container_status("ss-postgres")


# ---------------------------------------------------------------------------
# start_container
# ---------------------------------------------------------------------------


def test_start_container_succeeds():
    """GIVEN docker start exits 0
    WHEN start_container is called
    THEN no exception is raised.
    """
    mock_result = MagicMock(returncode=0, stdout="ss-postgres\n", stderr="")
    with patch("scripts.dev.dev_start.subprocess.run", return_value=mock_result):
        start_container("ss-postgres")  # should not raise


def test_start_container_raises_on_failure():
    """GIVEN docker start exits non-zero
    WHEN start_container is called
    THEN it raises RuntimeError with stderr.
    """
    mock_result = MagicMock(
        returncode=1,
        stdout="",
        stderr="Error response from daemon: container already started",
    )
    with patch("scripts.dev.dev_start.subprocess.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="Failed to start container"):
            start_container("ss-postgres")


def test_start_container_raises_on_timeout():
    """GIVEN docker start times out (hung daemon)
    WHEN start_container is called
    THEN it raises RuntimeError mentioning 'timed out'.
    """
    with patch(
        "scripts.dev.dev_start.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="docker", timeout=30),
    ):
        with pytest.raises(RuntimeError, match="timed out"):
            start_container("ss-postgres")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def test_main_exits_when_container_absent(capsys):
    """GIVEN check_container_status returns None (absent)
    WHEN main() is called
    THEN it prints an error and exits with code 1.
    """
    with (
        patch(
            "scripts.dev.dev_start.check_container_status",
            return_value=None,
        ),
        pytest.raises(SystemExit, match="1"),
    ):
        main()

    captured = capsys.readouterr()
    assert "does not exist" in captured.out


def test_main_starts_exited_container_and_execs(capsys):
    """GIVEN container is 'exited'
    WHEN main() is called
    THEN it calls start_container then os.execvp.
    """
    with (
        patch(
            "scripts.dev.dev_start.check_container_status",
            return_value="exited",
        ),
        patch("scripts.dev.dev_start.start_container") as mock_start,
        patch("scripts.dev.dev_start.os.execvp") as mock_exec,
    ):
        main()

    mock_start.assert_called_once_with("ss-postgres")
    mock_exec.assert_called_once_with("python", ["python", "app.py"])
