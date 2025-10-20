// Get references to the HTML elements
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');

// Function to add a message to the chat box
function addMessage(message, sender, isThinking = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');

    // Add sender-specific class
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');

    // Add thinking class if applicable
    if (isThinking) {
        messageDiv.classList.add('thinking');
    }

    const p = document.createElement('p');
    // Sanitize message slightly before displaying (basic protection)
    p.textContent = message; // Using textContent prevents HTML injection
    messageDiv.appendChild(p);

    chatBox.appendChild(messageDiv);
    // Scroll smoothly to the bottom of the chat box
    chatBox.scrollTo({
        top: chatBox.scrollHeight,
        behavior: 'smooth'
    });
    return messageDiv; // Return the created message element
}

// Function to handle sending a message
async function sendMessage() {
    const query = userInput.value.trim();
    if (query === '') return; // Don't send empty messages

    // Disable input and button while processing
    userInput.disabled = true;
    sendButton.disabled = true;

    // Display user's message
    addMessage(query, 'user');
    // Clear the input field immediately
    userInput.value = '';

    // Show a temporary "typing" message
    const thinkingMessage = addMessage('.', 'bot', true); // Pass true for thinking indicator

    try {
        // Send the query to the Flask backend API
        // Use '/api/chat' which matches the url_prefix in main.py
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        });

        // Remove the "thinking" message before displaying the actual response
        if (chatBox.contains(thinkingMessage)) {
            chatBox.removeChild(thinkingMessage);
        }

        if (!response.ok) {
            // Handle HTTP errors more gracefully
            let errorMsg = `Error: ${response.statusText} (${response.status})`;
            try {
                // Try to get more specific error from JSON response
                const errorData = await response.json();
                errorMsg = `Error: ${errorData.error || response.statusText} (${response.status})`;
            } catch (e) {
                // Ignore if response body is not JSON or empty
                console.warn("Could not parse error response as JSON.");
            }
            addMessage(errorMsg, 'bot');
            console.error('API Error:', errorMsg);

        } else {
            const data = await response.json();
            // Display the bot's response
            addMessage(data.response || "Sorry, I received an empty response.", 'bot');
        }

    } catch (error) {
         // Ensure thinking message is removed even if there's a network error
        if (chatBox.contains(thinkingMessage)) {
             chatBox.removeChild(thinkingMessage);
        }
        console.error('Network or fetch error:', error);
        addMessage('Sorry, there was a problem connecting to the server. Please try again.', 'bot');
    } finally {
        // Re-enable input and button
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus(); // Set focus back to input field
    }
}

// Event listener for the send button
sendButton.addEventListener('click', sendMessage);

// Event listener for pressing Enter in the input field
userInput.addEventListener('keypress', function(event) {
    // Check if Enter key was pressed without the Shift key
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault(); // Prevent default Enter behavior (like adding a newline)
        // Only send if the button is not disabled (i.e., not already sending)
        if (!sendButton.disabled) {
             sendMessage();
        }
    }
});

// Set focus to the input field when the page loads
userInput.focus();