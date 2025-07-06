# app/__init__.py
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

from app.config import Config
from app.routes.api import api_bp

# Import Blueprints
from app.routes.main import main_bp
from app.routes.views import views_bp
from app.state import (
    UNMATCHED,
    completed_results,
    current_progress,
    progress_lock,
    unmatched_lock,
)
from app.utils import REQUEST_CACHE, REQUEST_CACHE_TIMEOUT


def create_app():
    # Explicitly define template_folder and static_folder relative to this file's location
    app = Flask(
        __name__,
        template_folder="../templates",  # Points to <project_root>/templates
        static_folder="../static",  # Points to <project_root>/static
    )
    app.config.from_object(Config)

    # Ensure the logs directory exists
    os.makedirs("logs", exist_ok=True)

    # Setup logging configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(threadName)s] [%(levelname)s] %(message)s",
        handlers=[
            RotatingFileHandler(
                "logs/app_debug.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
                mode="a",
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Adjust log levels based on debug mode
    if not app.config["DEBUG_MODE"]:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("aiohttp.client").setLevel(logging.WARNING)
    else:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("aiohttp.client").setLevel(logging.INFO)

    logging.info(f"ScrobbleScope starting up, debug mode: {app.config['DEBUG_MODE']}")

    # Make {{ current_year }} available globally in all templates.
    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now().year}

    # Ensure API keys are present
    def ensure_api_keys():
        if not (
            app.config["LASTFM_API_KEY"]
            and app.config["SPOTIFY_CLIENT_ID"]
            and app.config["SPOTIFY_CLIENT_SECRET"]
        ):
            raise RuntimeError("Missing API keys! Check your .env file.")

    ensure_api_keys()

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/")
    app.register_blueprint(views_bp, url_prefix="/")

    # Reconfigure stdout/stderr for Windows cmd (if needed)
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    os.system("")

    return app
