async function initChat() {
    try {
        const response = await fetch("/api/profile-config");
        const apiData = await response.json();
        const qaArray = apiData?.qaData ?? [];
        return qaArray;
    } catch (error) {
        console.error('Failed to load QA data:', error);
        return [];
    }
}

// Add this at the beginning of your script section
function handleScroll() {
    if (window.innerWidth <= 768) { // Only for mobile screens
        const chatboxIcon = document.querySelector('.chatbox-icon');
        const footer = document.querySelector('footer');

        if (footer) {
            const footerRect = footer.getBoundingClientRect();
            const isFooterVisible = footerRect.top < window.innerHeight;

            if (isFooterVisible) {
                chatboxIcon.classList.add('hide');
            } else {
                chatboxIcon.classList.remove('hide');
            }
        }
    }
}

// Add scroll event listener
window.addEventListener('scroll', handleScroll);
window.addEventListener('resize', handleScroll);

// Initial check
window.addEventListener('load', handleScroll);

const cacheMessage = 'chatMessagesCache';
const cacheChatboxVisible = 'chatboxVisible';

function initializeChatOptions(qaArray = []) {
    const chatOptions = document.getElementById("chatOptions");
    qaArray.forEach(item => {
        const button = document.createElement("button");
        button.textContent = item.question;
        button.onclick = () => sendPredefinedMessage(item.question, qaArray);
        chatOptions?.appendChild(button);
    });
}

function toggleChatbox() {
    const modal = document.getElementById("chatboxModal");

    if (modal) {
        const isVisible = modal.style.display === "block";
        modal.style.display = isVisible ? "none" : "block";
        localStorage.setItem(cacheChatboxVisible, !isVisible);
    }
}

function sendMessage() {
    const input = document.getElementById("chatInput");
    const message = input.value.trim();
    if (message) {
        displayMessage(message, "", "black");
        input.value = "";
        cacheMessages(message);
        updateClearChatButtonVisibility();
    }
}

function sendPredefinedMessage(question, data = []) {
    displayMessage(question, "transparent", "black");
    const answer = getAutomaticAnswer(question, data);
    displayMessage(answer, "", "black");
    cacheMessages(question);
    cacheMessages(answer);
    updateClearChatButtonVisibility();
}

function getAutomaticAnswer(question, qaArray = []) {
    const qa = qaArray.find(item => item.question === question);
    if (qa) {
        let answer = qa.answer;
        if (answer.includes("{age}")) {
            answer = answer.replace("{age}", calculateAge());
        }

        return answer;
    }
    return null;
}

function displayMessage(message, backgroundColor = '', color = '', typeEffect = true) {
    const chatMessages = document.getElementById("chatMessages");
    const messageElement = document.createElement("div");
    messageElement.classList.add("chat-message");

    if (backgroundColor !== 'transparent') {
        // If background is not transparent, apply typing effect
        chatMessages.appendChild(messageElement);
        addTypingEffect(messageElement, message, typeEffect);
    } else {
        // Otherwise, display message instantly
        messageElement.textContent = 'Q: ' + message;
        chatMessages.appendChild(messageElement);
    }

    if (backgroundColor) {
        messageElement.style.backgroundColor = backgroundColor;
    }

    if (color) {
        messageElement.style.color = color;
    }
}

function addTypingEffect(element, text, typeEffect = true) {
    let index = 0;

    function typeNextCharacter() {
        if (index < text.length) {
            element.textContent += text.charAt(index);
            index++;
            setTimeout(typeNextCharacter, 50); // Adjust speed as needed
        }
    }

    if (!typeEffect) {
        element.textContent = text;
    } else {
        typeNextCharacter();
    }
}

function cacheMessages(message) {
    let cachedMessages = JSON.parse(localStorage.getItem(cacheMessage)) || [];
    cachedMessages.push(message);
    localStorage.setItem(cacheMessage, JSON.stringify(cachedMessages));
}

function loadCachedChat(qaArray = []) {
    const cachedMessages = JSON.parse(localStorage.getItem(cacheMessage)) || [];
    cachedMessages.forEach(message => displayMessage(message, qaArray.find(item => item.question == message) ? 'transparent' : '', "black", false));

    const chatboxVisible = localStorage.getItem(cacheChatboxVisible) === 'true';
    const modal = document.getElementById("chatboxModal");
    if (modal) {
        modal.style.display = chatboxVisible ? "block" : "none";
    }

    updateClearChatButtonVisibility();
}

function clearChat() {
    localStorage.removeItem(cacheMessage);
    const chatMessages = document.getElementById("chatMessages");
    chatMessages.innerHTML = '';
    updateClearChatButtonVisibility();
}

function updateClearChatButtonVisibility() {
    const cachedMessages = JSON.parse(localStorage.getItem(cacheMessage)) || [];
    const clearChatButton = document.getElementById("clearChat");
    if (clearChatButton) {
        clearChatButton.style.display = cachedMessages.length > 0 ? "block" : "none";
    }
}

window.onload = async () => {
    const chatBoxHeader = document.querySelector('.chatbox-header');
    const chatBoxBody = document.querySelector('.chatbox-body');
    chatBoxHeader.style.display = 'none';
    chatBoxBody.style.display = 'none'
    showLoading();
    const chatData = await initChat();
    initializeChatOptions(chatData);
    loadCachedChat(chatData);
    hideLoading();
    chatBoxHeader.style.display = 'flex';
    chatBoxBody.style.display = 'flex'
};