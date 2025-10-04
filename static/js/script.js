// Auto-resize textarea
function initializeAutoResize() {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    }
}

// Form submission handler
function initializeFormHandler() {
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await sendMessage();
        });
    }
}

// Enter key handler
function initializeEnterKeyHandler() {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

// Message actions (copy functionality)
function initializeMessageActions() {
    document.addEventListener('click', function(e) {
        if (e.target.closest('.message')) {
            const message = e.target.closest('.message');
            copyMessageToClipboard(message);
        }
    });
}

// Suggestion chips
function insertSuggestion(text) {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = text;
        messageInput.focus();
        // Trigger resize
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    }
}

// Clear chat function
function clearChat() {
    if (confirm('Are you sure you want to clear the chat?')) {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = `
            <div class="message bot-message">
                <div class="message-content">
                    <strong>👋 Welcome to your AI Travel Assistant!</strong><br><br>
                    I can help you with:<br>
                    • 🗺️ Trip planning & itineraries<br>
                    • 🏨 Hotel recommendations<br>
                    • 🍽️ Restaurant suggestions<br>
                    • 🚗 Transportation options<br>
                    • 🎭 Cultural activities<br><br>
                    How can I assist with your travel plans today?
                </div>
                <div class="message-time">Just now</div>
            </div>
        `;
        scrollToBottom();
    }
}

// Copy message to clipboard
async function copyMessageToClipboard(messageElement) {
    const messageContent = messageElement.querySelector('.message-content').textContent;
    try {
        await navigator.clipboard.writeText(messageContent);

        // Show temporary copy feedback
        const originalBg = messageElement.style.background;
        messageElement.style.background = 'var(--primary-color)';
        messageElement.style.color = 'white';

        setTimeout(() => {
            messageElement.style.background = originalBg;
            messageElement.style.color = '';
        }, 500);

    } catch (err) {
        console.log('Failed to copy message');
    }
}

// Send message to backend
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Show typing indicator
    showTypingIndicator();

    // Disable send button
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;

    try {
        const response = await fetch('/data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ data: message })
        });

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator();

        if (data.response) {
            addMessage('bot', data.message || data.response);
        } else {
            addMessage('bot', 'Sorry, I encountered an error. Please try again.');
        }
    } catch (error) {
        removeTypingIndicator();
        addMessage('bot', 'Connection error. Please check your internet connection.');
    }

    sendButton.disabled = false;
}

// Add message to chat
function addMessage(sender, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = formatMessage(content);

    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

    messageDiv.appendChild(messageContent);
    messageDiv.appendChild(messageTime);
    chatMessages.appendChild(messageDiv);

    scrollToBottom();
}

// Format message content
function formatMessage(content) {
    // Basic markdown formatting
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

// Show typing indicator
function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Scroll to bottom of chat
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Initialize all event listeners when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeAutoResize();
    initializeFormHandler();
    initializeEnterKeyHandler();
    initializeMessageActions();
    scrollToBottom();
});

