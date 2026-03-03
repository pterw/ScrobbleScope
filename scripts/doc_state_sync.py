#!/usr/bin/env python3
"""Entry point for doc_state_sync. Delegates entirely to docsync.cli."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docsync.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
