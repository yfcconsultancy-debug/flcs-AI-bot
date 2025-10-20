from flask import Flask, send_from_directory, render_template
import os
# Import the chat Blueprint
try:
    from app.routes.chat import chat_bp
except ImportError as e:
     print(f"Could not import chat blueprint: {e}")
     chat_bp = None # Allows app to start but API won't work

# --- Flask App Setup ---
# Determine the base directory of the 'app' package
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Create the Flask application instance
# Explicitly set template and static folders relative to APP_DIR
app = Flask(__name__,
            template_folder=os.path.join(APP_DIR, 'templates'),
            static_folder=os.path.join(APP_DIR, 'static'),
            static_url_path='/static' # Ensure static URL path is correctly set
           )

# Register the chat Blueprint if it was imported successfully
if chat_bp:
    app.register_blueprint(chat_bp, url_prefix='/api')
    print("Chat API blueprint registered at /api/chat.")
else:
    print("Chat API blueprint FAILED to register.")


# --- Routes ---
# Route to serve the main HTML page
@app.route('/')
def serve_index():
    # Use render_template which automatically looks in template_folder
    try:
        # render_template finds index.html inside the configured template_folder
        return render_template('index.html')
    except Exception as e:
        print(f"Error rendering index.html: {e}")
        return "Error loading page.", 500

# Flask handles static files automatically if static_folder and static_url_path are set correctly.
# This explicit route might not be necessary but is kept for clarity/fallback.
@app.route('/static/<path:filename>')
def serve_static(filename):
    # send_from_directory needs the absolute path to the static folder
    return send_from_directory(app.static_folder, filename)

# --- Server Start ---
# Start the server if this file is run directly
if __name__ == '__main__':
    print("Starting Flask server...")
    # Use host='0.0.0.0' to make it accessible on your network (optional)
    # Use port 5000 and enable debug mode for development
    app.run(debug=True, host='127.0.0.1', port=5000)