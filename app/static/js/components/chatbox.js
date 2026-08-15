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

function syncChatViewportHeight() {
    const vh = window.visualViewport?.height || window.innerHeight;
    document.documentElement.style.setProperty('--chat-viewport-height', `${Math.round(vh)}px`);
}

window.addEventListener('resize', syncChatViewportHeight);
window.addEventListener('orientationchange', syncChatViewportHeight);
window.visualViewport?.addEventListener('resize', syncChatViewportHeight);
window.visualViewport?.addEventListener('scroll', syncChatViewportHeight);

const cacheMessage = 'chatMessagesCache';
const cacheChatboxVisible = 'chatboxVisible';
const cacheChatOptionsCollapsed = 'chatOptionsCollapsed';
const BOT_TYPING_DELAY_MS = 320;
const cacheChatMuted = 'chatMuted';
const chatboxI18n = window.chatboxI18n || {};
let chatQaDataCache = [];
let typingIndicatorRow = null;
let chatSpeech = null;
let chatMuted = localStorage.getItem(cacheChatMuted) === 'true';

function stopChatSpeech() {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    chatSpeech = null;
}

function speakChatAnswer(text) {
    if (!("speechSynthesis" in window) || chatMuted || !text) return;
    window.speechSynthesis.cancel();
    const speech = new SpeechSynthesisUtterance(text);
    const language = typeof window.getVoiceLocale === "function"
        ? window.getVoiceLocale(window.pageLocale || "en")
        : "en-US";
    const voices = window.speechSynthesis.getVoices();
    const maleVoice = voices.find(
        (voice) =>
            voice.lang === language &&
            (voice.name.toLowerCase().includes("male") || voice.gender === "male")
    );
    if (maleVoice) {
        speech.voice = maleVoice;
    } else {
        speech.lang = language;
    }
    speech.pitch = 1;
    speech.rate = 1;
    speech.volume = 1;
    chatSpeech = speech;
    window.speechSynthesis.speak(speech);
}

function syncChatMuteToggle() {
    const toggle = document.getElementById("chatMuteToggle");
    if (!toggle) return;
    const icon = toggle.querySelector("ion-icon");
    if (icon) icon.setAttribute("name", chatMuted ? "volume-mute-outline" : "volume-high-outline");
    toggle.setAttribute("aria-pressed", String(chatMuted));
    toggle.setAttribute("aria-label", tChat(chatMuted ? "unmuteAria" : "muteAria", ""));
}

function toggleChatMute() {
    chatMuted = !chatMuted;
    localStorage.setItem(cacheChatMuted, String(chatMuted));
    if (chatMuted) stopChatSpeech();
    syncChatMuteToggle();
}

function tChat(key, fallback = "") {
    const value = chatboxI18n[key];
    return typeof value === "string" && value.length ? value : fallback;
}

function hideHelpCardIfHasMessages() {
    const helpCard = document.querySelector(".chatbox-help-card");
    const chatMessages = document.getElementById("chatMessages");
    if (!helpCard || !chatMessages) return;
    if (chatMessages.children.length > 0) {
        helpCard.style.display = "none";
    }
}

function scrollChatToBottom(behavior = "smooth") {
    const chatMessages = document.getElementById("chatMessages");
    if (!chatMessages) return;

    chatMessages.scrollTo({
        top: chatMessages.scrollHeight,
        behavior,
    });
}

function formatChatTime(timestamp = Date.now()) {
    try {
        return new Date(timestamp).toLocaleTimeString([], {
            hour: "numeric",
            minute: "2-digit",
        });
    } catch {
        return "";
    }
}

function getRoleLabel(role = "bot") {
    return role === "user"
        ? tChat("roleYou", "You")
        : tChat("roleBot", "AI Assistant");
}

function createMessageRow(role = "bot", timestamp = Date.now()) {
    const row = document.createElement("div");
    row.className = `chat-message-row ${role === "user" ? "is-user" : "is-bot"}`;
    row.dataset.role = role;

    const meta = document.createElement("div");
    meta.className = "chat-message-meta";

    const name = document.createElement("span");
    name.className = "chat-message-meta__name";
    name.textContent = getRoleLabel(role);

    const dot = document.createElement("span");
    dot.className = "chat-message-meta__dot";
    dot.textContent = "•";

    const time = document.createElement("span");
    time.className = "chat-message-meta__time";
    time.textContent = formatChatTime(timestamp);

    meta.appendChild(name);
    meta.appendChild(dot);
    meta.appendChild(time);

    const bubble = document.createElement("div");
    bubble.classList.add("chat-message");
    bubble.classList.add(role === "user" ? "chat-message-header" : "chat-message-answer");

    row.appendChild(meta);
    row.appendChild(bubble);

    return { row, bubble };
}

function setChatOptionsCollapsed(collapsed, persist = true) {
    const panel = document.getElementById("chatOptionsPanel");
    const toggle = document.getElementById("chatOptionsToggle");
    if (!panel || !toggle) return;

    panel.classList.toggle("is-collapsed", Boolean(collapsed));
    toggle.setAttribute("aria-expanded", String(!collapsed));

    if (persist) {
        localStorage.setItem(cacheChatOptionsCollapsed, String(Boolean(collapsed)));
    }
}

function toggleChatOptions() {
    const panel = document.getElementById("chatOptionsPanel");
    if (!panel) return;
    const collapsed = panel.classList.contains("is-collapsed");
    setChatOptionsCollapsed(!collapsed, true);
}

function updateChatOptionsCount(count = 0) {
    const countEl = document.getElementById("chatOptionsCount");
    if (countEl) {
        countEl.textContent = String(count);
    }
}

function showTypingIndicator() {
    const chatMessages = document.getElementById("chatMessages");
    if (!chatMessages || typingIndicatorRow) return;

    const { row, bubble } = createMessageRow("bot", Date.now());
    row.classList.add("chat-message-row--typing");
    bubble.innerHTML = `
        <span class="chat-typing-indicator" aria-label="${tChat("typingAria", "Typing")}">
            <span class="chat-typing-indicator__dot"></span>
            <span class="chat-typing-indicator__dot"></span>
            <span class="chat-typing-indicator__dot"></span>
        </span>
    `;

    typingIndicatorRow = row;
    chatMessages.appendChild(row);
    hideHelpCardIfHasMessages();
    scrollChatToBottom("smooth");
}

function removeTypingIndicator() {
    if (typingIndicatorRow?.parentElement) {
        typingIndicatorRow.parentElement.removeChild(typingIndicatorRow);
    }
    typingIndicatorRow = null;
}

function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function initializeChatOptions(qaArray = []) {
    const chatOptions = document.getElementById("chatOptions");
    if (!chatOptions) return;

    chatOptions.innerHTML = "";
    qaArray.forEach(item => {
        const button = document.createElement("button");
        button.textContent = item.question;
        button.onclick = () => sendPredefinedMessage(item.question, qaArray);
        chatOptions.appendChild(button);
    });

    updateChatOptionsCount(qaArray.length);
}

function toggleChatbox() {
    const modal = document.getElementById("chatboxModal");

    if (modal) {
        const isVisible = modal.style.display === "flex";
        modal.style.display = isVisible ? "none" : "flex";
        localStorage.setItem(cacheChatboxVisible, !isVisible);
        if (isVisible) stopChatSpeech();
    }
}

async function sendMessage() {
    const input = document.getElementById("chatInput");
    if (!input) return;

    const message = input.value.trim();
    if (message) {
        setChatOptionsCollapsed(true, true);

        const userTimestamp = Date.now();
        displayMessage(message, "transparent", "black", true, { role: "user", timestamp: userTimestamp });
        cacheMessages(message, "user", userTimestamp);
        input.value = "";

        const answer = getAutomaticAnswerSmart(message, chatQaDataCache);
        if (answer) {
            showTypingIndicator();
            speakChatAnswer(answer);
            await wait(BOT_TYPING_DELAY_MS);
            removeTypingIndicator();
            const botTimestamp = Date.now();
            displayMessage(answer, "", "black", true, { role: "bot", timestamp: botTimestamp });
            cacheMessages(answer, "bot", botTimestamp);
        }

        updateClearChatButtonVisibility();
    }
}

async function sendPredefinedMessage(question, data = []) {
    setChatOptionsCollapsed(true, true);

    const userTimestamp = Date.now();
    displayMessage(question, "transparent", "black", true, { role: "user", timestamp: userTimestamp });
    const answer = getAutomaticAnswer(question, data);
    cacheMessages(question, "user", userTimestamp);

    showTypingIndicator();
    speakChatAnswer(answer);
    await wait(BOT_TYPING_DELAY_MS);
    removeTypingIndicator();

    const botTimestamp = Date.now();
    displayMessage(answer, "", "black", true, { role: "bot", timestamp: botTimestamp });
    cacheMessages(answer, "bot", botTimestamp);
    updateClearChatButtonVisibility();
}

function handleChatInputKeydown(event) {
    if (!event) return;

    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
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

function getAutomaticAnswerSmart(question, qaArray = []) {
    const exact = getAutomaticAnswer(question, qaArray);
    if (exact) return exact;

    const normalized = (question || "").trim().toLowerCase();
    if (!normalized) return null;

    const greetingPatterns = [
        /\bhi\b/,
        /\bhello\b/,
        /\bhey\b/,
        /\bhola\b/,
        /\bkumusta\b/,
        /\bgood\s*morning\b/,
        /\bgood\s*afternoon\b/,
        /\bgood\s*evening\b/,
        /\bgood\s*day\b/,
    ];

    const isGreeting = greetingPatterns.some(pattern => pattern.test(normalized));
    if (isGreeting) {
        return tChat(
            "greetingFallback",
            "Hi! Welcome to my portfolio chat. You can ask me something directly or use the quick questions below."
        );
    }

    const partial = qaArray.find(item => {
        const q = (item?.question || "").toLowerCase();
        return q.includes(normalized) || normalized.includes(q);
    });

    if (partial?.answer) {
        let answer = partial.answer;
        if (answer.includes("{age}")) {
            answer = answer.replace("{age}", calculateAge());
        }
        return answer;
    }

    return tChat(
        "unknownFallback",
        "I can answer the suggested questions below. Try selecting one of the quick options."
    );
}

function displayMessage(message, backgroundColor = '', color = '', typeEffect = true, options = {}) {
    const chatMessages = document.getElementById("chatMessages");
    if (!chatMessages) return;
    const role = options.role || (backgroundColor === "transparent" ? "user" : "bot");
    const timestamp = options.timestamp || Date.now();
    const { row, bubble: messageElement } = createMessageRow(role, timestamp);

    chatMessages.appendChild(row);
    hideHelpCardIfHasMessages();

    if (role !== "user") {
        addTypingEffect(messageElement, message, typeEffect);
    } else {
        messageElement.textContent = tChat("questionPrefix", "Q: ") + message;
        scrollChatToBottom("smooth");
    }

    if (backgroundColor) {
        messageElement.style.backgroundColor = backgroundColor;
    }

    if (color) {
        messageElement.style.color = color;
    }

    scrollChatToBottom("smooth");
}

function addTypingEffect(element, text, typeEffect = true) {
    let index = 0;

    function typeNextCharacter() {
        if (index < text.length) {
            element.textContent += text.charAt(index);
            index++;
            const chatMessages = document.getElementById("chatMessages");
            if (chatMessages) {
                scrollChatToBottom("auto");
            }
            setTimeout(typeNextCharacter, 50); // Adjust speed as needed
        }
    }

    if (!typeEffect) {
        element.textContent = text;
        scrollChatToBottom("auto");
    } else {
        typeNextCharacter();
    }
}

function cacheMessages(message, role = "bot", timestamp = Date.now()) {
    let cachedMessages = JSON.parse(localStorage.getItem(cacheMessage)) || [];
    cachedMessages.push({ text: message, role, timestamp });
    localStorage.setItem(cacheMessage, JSON.stringify(cachedMessages));
}

function loadCachedChat(qaArray = []) {
    const cachedMessages = JSON.parse(localStorage.getItem(cacheMessage)) || [];
    cachedMessages.forEach(entry => {
        if (typeof entry === "string") {
            displayMessage(entry, qaArray.find(item => item.question == entry) ? 'transparent' : '', "black", false);
            return;
        }

        if (!entry || typeof entry !== "object") return;
        const text = entry.text ?? "";
        const role = entry.role ?? "bot";
        const timestamp = entry.timestamp ?? Date.now();
        displayMessage(text, role === "user" ? "transparent" : "", "black", false, { role, timestamp });
    });
    hideHelpCardIfHasMessages();

    const chatboxVisible = localStorage.getItem(cacheChatboxVisible) === 'true';
    const modal = document.getElementById("chatboxModal");
    if (modal) {
        modal.style.display = chatboxVisible ? "flex" : "none";
    }

    const isCollapsed = localStorage.getItem(cacheChatOptionsCollapsed) === "true";
    setChatOptionsCollapsed(isCollapsed, false);

    updateClearChatButtonVisibility();
}

function clearChat() {
    localStorage.removeItem(cacheMessage);
    removeTypingIndicator();
    stopChatSpeech();
    const chatMessages = document.getElementById("chatMessages");
    if (chatMessages) {
        chatMessages.innerHTML = '';
    }
    const helpCard = document.querySelector(".chatbox-help-card");
    if (helpCard) helpCard.style.display = '';
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
    syncChatViewportHeight();

    const chatBoxHeader = document.querySelector('.chatbox-header');
    const chatBoxBody = document.querySelector('.chatbox-body');
    chatBoxHeader.style.display = 'none';
    chatBoxBody.style.display = 'none'
    showTripleLoading?.();
    const chatData = await initChat();
    chatQaDataCache = chatData;
    initializeChatOptions(chatData);
    loadCachedChat(chatData);
    hideTripleLoading?.();
    chatBoxHeader.style.display = 'flex';
    chatBoxBody.style.display = 'flex';
    syncChatMuteToggle();
};
