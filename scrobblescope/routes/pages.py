"""The home page."""

import logging

from flask import render_template, request

from scrobblescope import routes as _routes

bp = _routes.bp


@bp.route("/", methods=["GET"])
def home():
    """Serve the home page"""
    logging.info("Serving index.html as the homepage.")
    initial_mode = "heatmap" if request.args.get("mode") == "heatmap" else "album"
    return render_template(
        "index.html",
        initial_mode=initial_mode,
        initial_heatmap_job=None,
    )
