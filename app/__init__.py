from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path

from flask import Flask


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = __import__('os').getenv('SECRET_KEY', 'dev')

    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now().year}

    # Register blueprints (currently empty)
    from .routes.main import main_bp

    app.register_blueprint(main_bp)
    return app


# Load legacy functions for tests from the root app.py
_root_path = Path(__file__).resolve().parent.parent / "app.py"
spec = importlib.util.spec_from_file_location("legacy_app", _root_path)
legacy_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_app)

check_user_exists = legacy_app.check_user_exists
normalize_name = legacy_app.normalize_name

# Provide the legacy app object for backward compatibility
app = legacy_app.app
