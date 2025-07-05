import os
import webbrowser

from app import create_app

# Create the application instance using the factory
app = create_app()

if __name__ == "__main__":
    # This check prevents the reloader from running this block twice.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        url = "http://127.0.0.1:5000/"
        print(f"🌐 Your app is live at: {url}")
        webbrowser.open(url)

    # Starts the server in debug mode with auto-reloading
    app.run(host="127.0.0.1", port=5000, debug=True)
