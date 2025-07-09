// static/js/script.js

document.addEventListener('DOMContentLoaded', () => {

    // ===================================
    // === NAVIGATION & HEADER LOGIC ===
    // ===================================
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    const navLinks = document.querySelectorAll('.nav-link');

    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
    });

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (navMenu.classList.contains('active')) {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
            }
        });
    });
    
    const header = document.querySelector('.header');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.1)';
        } else {
            header.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.05)';
        }
    });

    // ===================================
    // === CHATBOT WIDGET JAVASCRIPT ===
    // ===================================
    const chatButton = document.getElementById('chat-widget-button');
    const chatContainer = document.getElementById('chat-widget-container');
    const closeChatButton = document.getElementById('close-chat-widget');
    const chatForm = document.getElementById('chat-input-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    // Toggle chat widget visibility
    chatButton.addEventListener('click', () => {
        chatContainer.classList.toggle('show-widget');
    });

    closeChatButton.addEventListener('click', () => {
        chatContainer.classList.remove('show-widget');
    });

    // Handle form submission
    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const userInput = chatInput.value.trim();

        if (!userInput) return;

        // Display user's message in the chat
        addMessage(userInput, 'user');
        chatInput.value = '';

        try {
            // Send user message to the Flask backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userInput }),
            });
            
            const data = await response.json();
            const botReply = data.response;

            // Display bot's reply in the chat
            addMessage(botReply, 'bot');

        } catch (error) {
            console.error('Error:', error);
            addMessage('Oops! Something went wrong. Please try again later.', 'bot');
        }
    });

    // Helper function to add a message to the chat window
    function addMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        messageElement.textContent = text;
        chatMessages.appendChild(messageElement);

        // Scroll to the bottom of the chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

}); // <-- THE LISTENER NOW CORRECTLY WRAPS EVERYTHING