from flask import Blueprint, request, jsonify
# Ensure core is importable
try:
    from app.chatbot.core import get_bot_response
except ImportError as e:
    print(f"Error importing chatbot core: {e}. Make sure core.py exists and has no errors.")
    # Define a placeholder function if import fails, so the app can still start (partially)
    def get_bot_response(query: str) -> str:
        return f"Chatbot core module not loaded correctly. Import error: {e}"

# Create a 'Blueprint' - a way to organize routes
chat_bp = Blueprint('chat', __name__)

# Define the route '/chat' that accepts POST requests
@chat_bp.route('/chat', methods=['POST'])
def handle_chat():
    # Get the JSON data sent from the frontend
    data = request.get_json()

    # Check if the 'query' key exists in the JSON
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    user_query = data.get('query') # Use .get for safer access

    if not isinstance(user_query, str) or not user_query.strip():
         return jsonify({"error": "'query' must be a non-empty string"}), 400

    # Call your chatbot function from core.py
    try:
        bot_response = get_bot_response(user_query)
        # Return the bot's response as JSON
        return jsonify({"response": bot_response})
    except Exception as e:
        print(f"Error handling chat request: {e}")
        return jsonify({"error": "Internal server error processing chat request"}), 500