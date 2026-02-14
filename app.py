# ==============================================================#  app.py — ScrobbleScope application factory
# ==============================================================

# Load environment variables once
from dotenv import load_dotenv

load_dotenv()

import logging

# Standard library imports
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import Flask

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
        # Main log file with rotation (1MB max size, keep 5 backup files)
        RotatingFileHandler(
            "logs/app_debug.log",
            maxBytes=1 * 1024 * 1024,  # 1MB Max Size
            backupCount=5,
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


def create_app():
    """Application factory for ScrobbleScope."""
    application = Flask(__name__)
    application.secret_key = os.getenv("SECRET_KEY", "dev")

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
