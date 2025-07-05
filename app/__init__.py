"""Flask application factory and public interface."""

from datetime import datetime

from flask import Flask

from config import Config, ensure_api_keys

from .routes.main import main_bp
from .services.lastfm_service import check_user_exists
from .utils import normalize_name


def create_app(testing: bool = False) -> Flask:
    """Construct and configure the Flask application."""

    if not testing:
        ensure_api_keys()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY

    @app.context_processor
    def inject_current_year() -> dict[str, int]:
        return {"current_year": datetime.now().year}

    app.register_blueprint(main_bp)
    return app


__all__ = ["create_app", "check_user_exists", "normalize_name"]
