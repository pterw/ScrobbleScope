# app/state.py

import threading

# Global state tracking (moved from app/__init__.py)
UNMATCHED = {}  # Track unmatched artist/album pairs
current_progress = {"progress": 0, "message": "Initializing...", "error": False}
completed_results = {}  # Shared cache for completed results

# Locks for thread-safe access to global state
progress_lock = threading.Lock()
unmatched_lock = threading.Lock()
