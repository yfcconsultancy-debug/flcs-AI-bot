# wsgi.py
import sys
import os

# Add the project root directory to the Python path
# Helps Vercel find the 'app' module during runtime
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"WSGI: Added {PROJECT_ROOT} to sys.path")

# Import the Flask app instance from app/main.py
try:
    # The variable must be named 'application' for Vercel's Python runtime
    from app.main import app as application
    print("WSGI: Successfully imported Flask app as 'application'.")
except ImportError as e:
    print(f"WSGI CRITICAL ERROR: Error importing Flask app: {e}")
    # Define a simple fallback app for debugging deployment issues
    from flask import Flask
    application = Flask(__name__)
    @application.route('/')
    def fallback():
        return f"Error: Could not load the main application. Import Error: {e}", 500
except Exception as e:
    print(f"WSGI CRITICAL ERROR: An unexpected error occurred during app import: {e}")
    import traceback
    traceback.print_exc()
    from flask import Flask
    application = Flask(__name__)
    @application.route('/')
    def fallback_unexpected():
        return f"Error: Unexpected error loading application: {e}", 500

# Optional block for local WSGI testing (not used by Vercel)
if __name__ == "__main__":
    print("Running WSGI entry point directly (for local testing only)")
    try:
        from waitress import serve
        print("Starting Waitress server on http://127.0.0.1:5001")
        serve(application, host='127.0.0.1', port=5001)
    except ImportError:
        print("Waitress not installed. Cannot run WSGI test server.")
        print("Install using: pip install waitress")
    except Exception as run_err:
        print(f"Error running WSGI test server: {run_err}")