# in dir for opening with python
import os
import webbrowser

from app import app
from scrobblescope.config import ensure_api_keys

if __name__ == "__main__":
    # Fail fast with a clear message, as app.py does, rather than serving pages
    # whose searches cannot reach Last.fm or Spotify.
    ensure_api_keys()

    # This check prevents the reloader from running this block twice.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        url = "http://127.0.0.1:5000/"
        # Plain ASCII: an emoji here crashed the launch whenever stdout was not a
        # UTF-8 console (a pipe, a redirect, or a cp1252 background shell).
        print(f"Your app is live at: {url}")
        # Opens the browser automatically
        webbrowser.open(url)

    # Starts the server in debug mode with auto-reloading
    app.run(host="127.0.0.1", port=5000, debug=True)
