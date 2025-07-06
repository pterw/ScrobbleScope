# app/routes/main.py

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def home():
    """Serve the home page"""
    return render_template("index.html")


@main_bp.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors with a nice error page"""
    return (
        render_template(
            "error.html",
            error="Page not found",
            message="The page you're looking for doesn't exist.",
        ),
        404,
    )


@main_bp.errorhandler(500)
def internal_error(e):
    """Handle 500 errors with a nice error page"""
    return (
        render_template(
            "error.html",
            error="Server Error",
            message="Something went wrong on our end. Please try again later.",
        ),
        500,
    )
