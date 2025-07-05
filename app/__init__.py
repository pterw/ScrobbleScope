# in app/__init__.py

import os
from datetime import datetime

from flask import Flask


# This is the main application factory function
def create_app():
    """Create and configure an instance of the Flask application."""

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
    )

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # This entire block MUST be indented inside create_app()
    # The @app.context_processor line decorates the function defined immediately below it.
    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now().year}

    # The return statement is the last line of the create_app() function
    return app
