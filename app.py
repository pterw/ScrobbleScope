# ==============================================================#  app.py — ScrobbleScope application factory
# ==============================================================

# Load environment variables once
from pathlib import Path

from dotenv import load_dotenv

# Use an explicit path anchored to this file so load_dotenv never depends
# on the working directory (which can differ in background terminals,
# Docker containers, or when invoked via dev_start.py).
load_dotenv(Path(__file__).resolve().parent / ".env")

# Standard library imports
import io
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

csrf = CSRFProtect()

if isinstance(sys.stderr, io.TextIOWrapper):
    sys.stderr.reconfigure(encoding="utf-8")

# Enable ANSI escape codes on Windows cmd
os.system("")

# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Setup logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s",
    handlers=[
        # Main log file with rotation: 2MB files, 10 backups = 20MB max.
        # Small files stay quick to open and search; 10 backups give enough
        # granular time-window chunks to cover a full load test session.
        # On Fly.io this file is ephemeral (wiped on restart/deploy);
        # stdout (below) is the canonical production log channel.
        RotatingFileHandler(
            "logs/app_debug.log",
            maxBytes=2 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
            mode="a",
        ),
        logging.StreamHandler(sys.stdout),
    ],
)

# Add start-up banner on application start
logging.info("=" * 80)
logging.info(f"ScrobbleScope Application Starting at {datetime.now().isoformat()}")
logging.info("=" * 80)

# Add an environment variable check for debug mode
debug_mode = os.getenv("DEBUG_MODE", "0") == "1"

# Adjust log levels based on debug mode
if not debug_mode:
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.client").setLevel(logging.WARNING)
else:
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.client").setLevel(logging.INFO)

# Log application start
logging.info(f"ScrobbleScope starting up, debug mode: {debug_mode}")

_KNOWN_WEAK_SECRETS = frozenset({"dev", "changeme_in_production", ""})
_MIN_SECRET_LENGTH = 16


def _validate_secret_key(secret_key: str, is_dev_mode: bool) -> None:
    """Validate SECRET_KEY strength at startup.

    Raises RuntimeError in production if the key is missing or insecure.
    Logs a warning in dev mode instead of failing hard.
    """
    is_weak = (
        not secret_key
        or secret_key in _KNOWN_WEAK_SECRETS
        or len(secret_key) < _MIN_SECRET_LENGTH
    )
    if not is_weak:
        return
    guidance = (
        "Set a strong SECRET_KEY "
        '(e.g., `python -c "import os; print(os.urandom(32).hex())"`)'
    )
    if is_dev_mode:
        logging.warning(
            "SECRET_KEY is missing or insecure. %s Continuing in dev mode.", guidance
        )
    else:
        raise RuntimeError(
            f"Refusing to start: SECRET_KEY is missing or insecure. {guidance}"
        )


def create_app():
    """Application factory for ScrobbleScope."""
    _raw_secret = os.getenv("SECRET_KEY", "")
    _validate_secret_key(_raw_secret, debug_mode)
    application = Flask(__name__)
    application.secret_key = _raw_secret or "dev"

    csrf.init_app(application)

    @application.after_request
    def add_security_headers(response):
        """Add standard HTTP security headers to all responses."""
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @application.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """Return a user-friendly error page on CSRF token validation failure."""
        logging.warning(f"CSRF validation failed: {e.description}")
        return (
            render_template(
                "error.html",
                error="Request Validation Failed",
                message="Your request could not be verified. Please try again.",
                details="If this keeps happening, try refreshing the page.",
            ),
            400,
        )

    from scrobblescope.routes import bp

    application.register_blueprint(bp)
    return application


# Module-level instance for backward compatibility with gunicorn app:app
app = create_app()

if __name__ == "__main__":
    import webbrowser

    from scrobblescope.config import ensure_api_keys

    ensure_api_keys()

    url = "http://127.0.0.1:5000/"
    print(f"Your app is live at: {url}")
    webbrowser.open(url)

    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
