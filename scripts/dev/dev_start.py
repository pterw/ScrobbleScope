#!/usr/bin/env python3
"""One-command local development startup with Postgres cache.

Checks the state of the ``ss-postgres`` Docker container, starts it if
needed, then replaces the current process with Flask (``python app.py``).
After this script exits, Flask is the process -- not a child of a wrapper.

Usage::

    python scripts/dev/dev_start.py

Prerequisites
-------------
* The ``ss-postgres`` Docker container must **already exist** (created via
  ``docker run``; see SESSION_CONTEXT Section 8 for the full command).
  This script starts/checks an existing container but does **not** create
  one from scratch.
* ``DATABASE_URL`` must be set in ``.env`` (or in the shell environment).
  Flask's ``load_dotenv()`` picks it up at startup automatically.

Scope
-----
Local development only.  This script has no effect on the Fly.io deployment
path.  Do **not** invoke it in CI or production.
"""

from __future__ import annotations

import os
import subprocess
import sys

# Docker container name for the local Postgres cache instance.
CONTAINER_NAME = "ss-postgres"


def check_container_status(container_name: str) -> str | None:
    """Return the Docker container's current state, or None if absent.

    Runs ``docker inspect --format={{.State.Status}} <name>`` and returns
    the raw status string reported by the Docker daemon.  Common values:

    * ``"running"``    -- container is up and accepting connections.
    * ``"exited"``     -- container has stopped; can be restarted.
    * ``"paused"``     -- container is paused.
    * ``"created"``    -- container exists but has never been started.
    * ``"restarting"`` / ``"dead"`` -- transient or error states.

    Returns ``None`` when Docker reports "No such object" (i.e., the
    container has not been created at all).  ``None`` is the sentinel for
    "run the docker run command to create the container first".

    Parameters
    ----------
    container_name : str
        The Docker container name to inspect (e.g. ``"ss-postgres"``).

    Returns
    -------
    str | None
        The status string from the Docker daemon, or ``None`` if the
        container does not exist.

    Raises
    ------
    RuntimeError
        If the ``docker`` executable is not found on ``PATH``.  Docker
        Desktop must be installed and running before this script is used.
    """
    try:
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "--format={{.State.Status}}",
                container_name,
            ],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "docker executable not found on PATH. "
            "Install Docker Desktop and ensure it is running."
        )

    if result.returncode != 0:
        stderr_lower = (result.stderr or "").lower()

        # Container genuinely does not exist -- caller prints docker run help.
        if "no such object" in stderr_lower:
            return None

        # Docker is installed but the daemon is not reachable or the user
        # lacks permissions -- raise so the error message is actionable.
        if (
            "cannot connect to the docker daemon" in stderr_lower
            or "is the docker daemon running" in stderr_lower
            or "permission denied" in stderr_lower
        ):
            details = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                "Docker daemon is not reachable or permissions are "
                f"insufficient while inspecting container "
                f"'{container_name}'.\nUnderlying error: {details}"
            )

        # Any other unexpected docker error.
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(
            f"Unexpected error while inspecting container "
            f"'{container_name}': {details}"
        )

    return result.stdout.strip()


def start_container(container_name: str) -> None:
    """Start an existing but stopped Docker container.

    Runs ``docker start <name>`` and waits for the command to complete.
    Only call this when the container exists and is not already running
    (``check_container_status`` returns ``"exited"`` or ``"paused"``).

    Parameters
    ----------
    container_name : str
        The Docker container name to start.

    Raises
    ------
    RuntimeError
        If ``docker start`` exits with a non-zero exit code, indicating
        that Docker could not start the container.
    """
    result = subprocess.run(
        ["docker", "start", container_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to start container '{container_name}': " f"{result.stderr.strip()}"
        )


def main() -> None:
    """Check the Postgres container state and launch Flask.

    Three-step startup flow:

    1. Inspect the ``ss-postgres`` container via
       :func:`check_container_status`.
    2. Branch on the reported status:

       * ``"running"``            -- already up; log and continue.
       * ``"exited"`` / ``"paused"`` -- call :func:`start_container`, log,
         and continue.
       * any other non-None value (e.g. ``"created"``, ``"dead"``) --
         print a warning and ``sys.exit(1)``; manual intervention needed.
       * ``None`` (container absent) -- print a clear error with the
         location of the ``docker run`` command and ``sys.exit(1)``.

    3. Replace the current process with Flask via ``os.execvp``.  Flask
       inherits the full environment so ``DATABASE_URL`` from ``.env`` is
       picked up automatically by ``load_dotenv()`` in ``app.py``.

    All status lines are prefixed ``[dev_start]`` for easy grep filtering
    in terminal output or log files.

    Raises
    ------
    RuntimeError
        Propagated from :func:`check_container_status` if ``docker`` is
        not on ``PATH``, or from :func:`start_container` if the container
        fails to start.
    """
    status = check_container_status(CONTAINER_NAME)

    if status == "running":
        print(f"[dev_start] {CONTAINER_NAME} already running")

    elif status in ("exited", "paused"):
        print(f"[dev_start] {CONTAINER_NAME} is {status} -- starting...")
        start_container(CONTAINER_NAME)
        print(f"[dev_start] started {CONTAINER_NAME}")

    elif status is None:
        print(
            f"[dev_start] ERROR: container '{CONTAINER_NAME}' does not exist.\n"
            "Create it first with the docker run command documented in:\n"
            "  .claude/SESSION_CONTEXT.md  (Section 8)\n"
            "then re-run this script."
        )
        sys.exit(1)

    else:
        # Unexpected states (e.g. "dead", "restarting", "created") require
        # manual intervention; do not attempt an automatic start.
        print(
            f"[dev_start] ERROR: {CONTAINER_NAME} is in unexpected state "
            f"'{status}'.\n"
            "Resolve the container state manually before starting the app."
        )
        sys.exit(1)

    print("[dev_start] launching Flask (app.py)...")

    # os.execvp replaces the current process image with Flask directly.
    # Prefer execvp over subprocess.Popen because:
    # - Flask becomes the process (not a child), so signals (Ctrl-C, SIGTERM)
    #   are delivered directly to Flask -- no wrapper process to clean up.
    # - The process tree is cleaner: one PID, correct title in ps / Task Mgr.
    os.execvp("python", ["python", "app.py"])


if __name__ == "__main__":
    main()
