"""Application factory for ScrobbleScope."""

from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from flask import Flask


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    try:
        app.config.from_object("config.Config")
    except Exception:
        pass

    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now().year}

    from .routes.main import bp as main_bp

    app.register_blueprint(main_bp)

    return app


# Import legacy application for backward compatibility
legacy_spec = spec_from_file_location(
    "legacy_app", Path(__file__).resolve().parents[1] / "app.py"
)
legacy_app = module_from_spec(legacy_spec)
legacy_spec.loader.exec_module(legacy_app)

legacy_app.app.template_folder = str(Path(__file__).resolve().parent / "templates")

app = legacy_app.app
check_user_exists = legacy_app.check_user_exists
normalize_name = legacy_app.normalize_name
