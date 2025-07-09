
document.addEventListener('DOMContentLoaded', () => {

  
   
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

   
    const chatButton = document.getElementById('chat-widget-button');
    const chatContainer = document.getElementById('chat-widget-container');
    const closeChatButton = document.getElementById('close-chat-widget');
    const chatForm = document.getElementById('chat-input-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    
    chatButton.addEventListener('click', () => {
        chatContainer.classList.toggle('show-widget');
    });

    closeChatButton.addEventListener('click', () => {
        chatContainer.classList.remove('show-widget');
    });

    chatForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const userInput = chatInput.value.trim();

        if (!userInput) return;

       
        addMessage(userInput, 'user');
        chatInput.value = '';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userInput }),
            });
            
            const data = await response.json();
            const botReply = data.response;

            
            addMessage(botReply, 'bot');

        } catch (error) {
            console.error('Error:', error);
            addMessage('Oops! Something went wrong. Please try again later.', 'bot');
        }
    });

    function addMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        messageElement.textContent = text;
        chatMessages.appendChild(messageElement);

       
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

}); 
