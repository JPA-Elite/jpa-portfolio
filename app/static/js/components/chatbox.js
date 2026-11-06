import { ChatService } from "../services/ChatService.js";

const chatService = new ChatService();

async function initChat() {
    try {
        const apiData = await chatService.fetchProfileConfig();
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
const cacheChatSession = 'chatSessionId';
const CHAT_TYPING_TICK_MS = 16;
const CHAT_TYPING_CHARS_PER_TICK = 3;
const CHATBOX_ANIM_MS = 550;
const cacheChatMuted = 'chatMuted';
const cacheChatMaximized = 'chatMaximized';
const chatboxI18n = window.chatboxI18n || {};
let chatQaDataCache = [];
let typingIndicatorRow = null;
let chatSpeech = null;
let chatMuted = localStorage.getItem(cacheChatMuted) === 'true';
let chatRequestPending = false;
let chatTypingActive = null;
let chatTypingToken = 0;
let chatStreamController = null;

function isChatSpeaking() {
    try {
        return ("speechSynthesis" in window) && window.speechSynthesis.speaking;
    } catch {
        return false;
    }
}

function updateChatStopButton() {
    const stopButton = document.getElementById("stopChat");
    const sendButton = document.getElementById("sendChat");
    const busy = Boolean(chatTypingActive) || isChatSpeaking() || Boolean(chatStreamController);
    if (stopButton) {
        if (busy) stopButton.removeAttribute("hidden");
        else stopButton.setAttribute("hidden", "");
    }
    if (sendButton) {
        if (busy) sendButton.setAttribute("hidden", "");
        else sendButton.removeAttribute("hidden");
    }
}

function cancelChatTyping() {
    chatTypingToken++;
    chatTypingActive = null;
    updateChatStopButton();
}

function stopChatResponse() {
    const active = chatTypingActive;
    cancelChatTyping();
    stopChatSpeech();
    if (chatStreamController) {
        chatStreamController.abort();
        chatStreamController = null;
    }
    updateChatStopButton();
    if (active && active.element) {
        active.element.textContent = active.text;
        linkifyChatMessage(active.element);
        scrollChatToBottom("auto");
    }
    updateChatStopButton();
}

function setChatComposerLoading(isLoading) {
    const input = document.getElementById("chatInput");
    const sendButton = document.getElementById("sendChat");
    const emojiToggle = document.getElementById("chatEmojiToggle");
    if (input) {
        input.disabled = Boolean(isLoading);
        input.setAttribute("aria-disabled", String(Boolean(isLoading)));
    }
    if (sendButton) {
        sendButton.disabled = Boolean(isLoading);
        sendButton.classList.toggle("is-loading", Boolean(isLoading));
        sendButton.setAttribute("aria-busy", String(Boolean(isLoading)));
    }
    if (emojiToggle) {
        emojiToggle.disabled = Boolean(isLoading);
        if (isLoading) closeChatEmojiPicker();
    }
    const chatOptionsPanel = document.getElementById("chatOptionsPanel");
    if (chatOptionsPanel) {
        chatOptionsPanel.style.display = isLoading ? "none" : "";
    }
    if (isLoading) {
        startChatTypingPlaceholder();
    } else {
        stopChatTypingPlaceholder();
    }
}

let chatPlaceholderText = "";
let chatPlaceholderTimer = null;
const CHAT_TYPING_DOTS = ["", ".", "..", "..."];

function startChatTypingPlaceholder() {
    const input = document.getElementById("chatInput");
    if (!input) return;
    if (!chatPlaceholderText) {
        chatPlaceholderText = input.placeholder;
    }
    const base = tChat("typingMessage", "Josh is thinking");
    let dotIndex = 0;
    const update = () => {
        input.placeholder = base + CHAT_TYPING_DOTS[dotIndex];
        dotIndex = (dotIndex + 1) % CHAT_TYPING_DOTS.length;
    };
    update();
    chatPlaceholderTimer = setInterval(update, 400);
}

function stopChatTypingPlaceholder() {
    if (chatPlaceholderTimer) {
        clearInterval(chatPlaceholderTimer);
        chatPlaceholderTimer = null;
    }
    const input = document.getElementById("chatInput");
    if (input && chatPlaceholderText) {
        input.placeholder = chatPlaceholderText;
    }
}

function getChatSessionId() {
    let sessionId = localStorage.getItem(cacheChatSession);
    if (!sessionId) {
        sessionId = (typeof crypto !== "undefined" && crypto.randomUUID)
            ? crypto.randomUUID()
            : "chat-" + Date.now() + "-" + Math.random().toString(36).slice(2);
        localStorage.setItem(cacheChatSession, sessionId);
    }
    return sessionId;
}

function stopChatSpeech() {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    chatSpeech = null;
    updateChatStopButton();
}

function chatLocaleAllowsSpeech() {
    const locale = String(window.pageLocale || "en").toLowerCase();
    return locale === "en" || locale.startsWith("en-") || locale.startsWith("en_");
}

function speakChatAnswer(text) {
    if (!("speechSynthesis" in window) || chatMuted || !text) return;
    if (!chatLocaleAllowsSpeech()) return;
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
    speech.onstart = () => updateChatStopButton();
    speech.onend = () => updateChatStopButton();
    speech.onerror = () => updateChatStopButton();
    chatSpeech = speech;
    window.speechSynthesis.speak(speech);
    updateChatStopButton();
}

function syncChatMuteToggle() {
    const toggle = document.getElementById("chatMuteToggle");
    if (!toggle) return;
    if (!chatLocaleAllowsSpeech()) {
        toggle.style.display = "none";
        return;
    }
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

function syncChatMaximizeToggle() {
    const modal = document.getElementById("chatboxModal");
    const toggle = document.getElementById("chatMaximizeToggle");
    if (!modal || !toggle) return;
    const isMaximized = modal.classList.contains("is-maximized");
    const icon = toggle.querySelector("ion-icon");
    if (icon) icon.setAttribute("name", isMaximized ? "contract-outline" : "expand-outline");
    toggle.setAttribute("aria-pressed", String(isMaximized));
    toggle.setAttribute("aria-label", tChat(isMaximized ? "minimizeAria" : "maximizeAria", isMaximized ? "Minimize chat" : "Maximize chat"));
}

function toggleChatMaximize() {
    const modal = document.getElementById("chatboxModal");
    if (!modal) return;
    const isMaximized = modal.classList.contains("is-maximized");
    modal.classList.toggle("is-maximized", !isMaximized);
    localStorage.setItem(cacheChatMaximized, String(!isMaximized));
    syncChatMaximizeToggle();
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
        : tChat("roleBot", "Josh");
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

function initializeChatOptions(qaArray = []) {
    const chatOptions = document.getElementById("chatOptions");
    if (!chatOptions) return;

    chatOptions.innerHTML = "";
    qaArray.slice(0, 10).forEach(item => {
        const button = document.createElement("button");
        button.textContent = item.display_question || item.question;
        button.onclick = () => sendPredefinedMessage(item.question, qaArray);
        chatOptions.appendChild(button);
    });

    updateChatOptionsCount(Math.min(qaArray.length, 10));
}

function toggleChatbox() {
    const modal = document.getElementById("chatboxModal");
    if (!modal) return;

    const willOpen = localStorage.getItem(cacheChatboxVisible) !== "true";

    if (modal.dataset.chatAnimTimer) {
        window.clearTimeout(Number(modal.dataset.chatAnimTimer));
        delete modal.dataset.chatAnimTimer;
    }
    modal.classList.remove("chatbox-modal--opening", "chatbox-modal--closing");
    void modal.offsetWidth;

    if (willOpen) {
        modal.classList.add("chatbox-modal--opening");
        modal.style.display = "flex";
        localStorage.setItem(cacheChatboxVisible, true);
        modal.dataset.chatAnimTimer = window.setTimeout(() => {
            modal.classList.remove("chatbox-modal--opening");
            delete modal.dataset.chatAnimTimer;
        }, CHATBOX_ANIM_MS);
    } else {
        stopChatSpeech();
        modal.classList.add("chatbox-modal--closing");
        localStorage.setItem(cacheChatboxVisible, false);
        modal.dataset.chatAnimTimer = window.setTimeout(() => {
            modal.style.display = "none";
            modal.classList.remove("chatbox-modal--closing");
            delete modal.dataset.chatAnimTimer;
        }, CHATBOX_ANIM_MS);
    }
}

async function fetchChatAnswer(message, onToken) {
    let streamed = false;
    const forward = (text) => {
        streamed = true;
        if (typeof onToken === "function") onToken(text);
    };
    const controller = typeof AbortController === "function" ? new AbortController() : null;
    chatStreamController = controller;
    updateChatStopButton();

    try {
        const data = await chatService.streamMessage(message, getChatSessionId(), forward, controller?.signal);
        if (data?.answer) return data.answer;
    } catch (error) {
        console.error("Failed to stream chat answer:", error);
    } finally {
        if (chatStreamController === controller) chatStreamController = null;
        updateChatStopButton();
    }

    if (streamed) return null;

    try {
        const data = await chatService.sendMessage(message, getChatSessionId());
        return data?.answer || null;
    } catch (error) {
        console.error("Failed to fetch chat answer:", error);
        return null;
    }
}

function startStreamingMessage() {
    const chatMessages = document.getElementById("chatMessages");
    if (!chatMessages) return null;
    const timestamp = Date.now();
    const { row, bubble } = createMessageRow("bot", timestamp);
    bubble.style.color = "black";
    chatMessages.appendChild(row);
    hideHelpCardIfHasMessages();
    scrollChatToBottom("auto");
    return { row, bubble, timestamp, text: "" };
}

async function runBotReply(message) {
    showTypingIndicator();
    let stream = null;

    const onToken = (text) => {
        if (!stream) {
            stream = startStreamingMessage();
            removeTypingIndicator();
        }
        if (!stream) return;
        stream.text += text;
        stream.bubble.textContent = stream.text;
        const chatMessages = document.getElementById("chatMessages");
        if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const answer = await fetchChatAnswer(message, onToken);
    removeTypingIndicator();

    const finalText = (answer || stream?.text || "").trim();
    if (!finalText) return;

    const botTimestamp = stream?.timestamp || Date.now();
    if (stream) {
        stream.bubble.textContent = finalText;
        linkifyChatMessage(stream.bubble);
        scrollChatToBottom("smooth");
    } else {
        displayMessage(finalText, "", "black", true, { role: "bot", timestamp: botTimestamp });
    }

    speakChatAnswer(finalText);
    cacheMessages(finalText, "bot", botTimestamp);
}

async function sendMessage() {
    const input = document.getElementById("chatInput");
    if (!input) return;

    const message = input.value.trim();
    if (message && !chatRequestPending) {
        chatRequestPending = true;
        setChatOptionsCollapsed(true, true);
        setChatComposerLoading(true);

        const userTimestamp = Date.now();
        displayMessage(message, "transparent", "black", true, { role: "user", timestamp: userTimestamp });
        cacheMessages(message, "user", userTimestamp);
        input.value = "";

        await runBotReply(message);

        setChatComposerLoading(false);
        chatRequestPending = false;
        updateClearChatButtonVisibility();
    }
}

async function sendPredefinedMessage(question, data = []) {
    if (chatRequestPending) return;
    chatRequestPending = true;
    setChatOptionsCollapsed(true, true);
    setChatComposerLoading(true);

    const userTimestamp = Date.now();
    displayMessage(question, "transparent", "black", true, { role: "user", timestamp: userTimestamp });
    cacheMessages(question, "user", userTimestamp);

    await runBotReply(question);

    setChatComposerLoading(false);
    chatRequestPending = false;
    updateClearChatButtonVisibility();
}

function handleChatInputKeydown(event) {
    if (!event) return;

    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        if (chatRequestPending) return;
        sendMessage();
    }
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

function linkifyChatMessage(element) {
    if (!element) return;
    const text = element.textContent || "";
    if (!text) return;

    const plainUrl = /https?:\/\/[^\s<>"']+/g;
    const markdownLink = /\[([^\]]+)\]\((https?:\/\/[^\s)]+|\/[^)\s]+)\)/g;
    if (!plainUrl.test(text) && !markdownLink.test(text)) return;
    plainUrl.lastIndex = 0;
    markdownLink.lastIndex = 0;

    const escapeHtml = (value) => String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    const absolute = (url) => {
        if (/^https?:\/\//i.test(url)) return url;
        return window.location.origin + (url.startsWith("/") ? url : "/" + url);
    };

    const linkify = (match) => {
        const url = match.replace(/[.,;:!?]+$/, "");
        const href = escapeHtml(url);
        return `<a href="${href}" target="_blank" rel="noopener noreferrer">${href}</a>`;
    };

    element.innerHTML = escapeHtml(text)
        .replace(markdownLink, (match, label, url) => {
            const href = escapeHtml(absolute(url));
            return `<a href="${href}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`;
        })
        .replace(plainUrl, linkify);
}

function addTypingEffect(element, text, typeEffect = true) {
    if (!typeEffect) {
        element.textContent = text;
        linkifyChatMessage(element);
        scrollChatToBottom("auto");
        return;
    }
    const token = ++chatTypingToken;
    chatTypingActive = { element, text };
    updateChatStopButton();
    let index = 0;

    function typeNextCharacter() {
        if (token !== chatTypingToken) return;
        if (index < text.length) {
            index = Math.min(index + CHAT_TYPING_CHARS_PER_TICK, text.length);
            element.textContent = text.slice(0, index);
            const chatMessages = document.getElementById("chatMessages");
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            setTimeout(typeNextCharacter, CHAT_TYPING_TICK_MS);
        } else {
            const active = chatTypingActive;
            chatTypingActive = null;
            updateChatStopButton();
            if (active) linkifyChatMessage(active.element);
        }
    }

    typeNextCharacter();
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

function wipeChatStorage() {
    localStorage.removeItem(cacheMessage);
    localStorage.removeItem(cacheChatSession);
}

function clearChat() {
    removeTypingIndicator();
    cancelChatTyping();
    stopChatSpeech();
    wipeChatStorage();
    updateClearChatButtonVisibility();

    const chatMessages = document.getElementById("chatMessages");
    const rows = chatMessages
        ? Array.from(chatMessages.querySelectorAll(".chat-message-row"))
        : [];
    if (rows.length === 0) return;

    const delayStep = 90;
    const maxDelaySteps = 14;
    rows.reverse().forEach((row, index) => {
        row.classList.add("chat-message-row--clearing");
        row.style.animationDelay = `${Math.min(index, maxDelaySteps) * delayStep}ms`;
    });

    setTimeout(() => {
        if (chatMessages) chatMessages.innerHTML = "";
        const helpCard = document.querySelector(".chatbox-help-card");
        if (helpCard) helpCard.style.display = "";
    }, Math.min(rows.length, maxDelaySteps) * delayStep + 500);
}

function updateClearChatButtonVisibility() {
    const cachedMessages = JSON.parse(localStorage.getItem(cacheMessage)) || [];
    const clearChatButton = document.getElementById("clearChat");
    if (clearChatButton) {
        clearChatButton.style.display = cachedMessages.length > 0 ? "block" : "none";
    }
}

function getChatEmojiElements() {
    return {
        input: document.getElementById("chatInput"),
        picker: document.getElementById("chatEmojiPicker"),
        toggle: document.getElementById("chatEmojiToggle"),
    };
}

function getSpeechRecognition() {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function getSpeechLocale() {
    const locale = (window.pageLocale || "en").toLowerCase();
    const map = {
        ceb: "ceb-PH",
        fil_ph: "fil-PH",
        fil: "fil-PH",
        fr: "fr-FR",
        en: "en-US",
    };
    return map[locale] || "en-US";
}

let chatRecognition = null;
let chatMicHintTimer = null;
let chatMicPermission = "prompt";

function flashChatMicHint(message) {
    const input = document.getElementById("chatInput");
    if (!input) return;
    const original = chatPlaceholderText || input.placeholder;
    input.placeholder = message;
    clearTimeout(chatMicHintTimer);
    chatMicHintTimer = setTimeout(() => {
        input.placeholder = original;
    }, 4000);
}

function setChatMicState(recording) {
    const micButton = document.getElementById("chatMicToggle");
    if (!micButton) return;
    micButton.classList.toggle("is-recording", Boolean(recording));
    micButton.setAttribute("aria-pressed", String(Boolean(recording)));
    const icon = micButton.querySelector("ion-icon");
    if (icon) icon.setAttribute("name", recording ? "mic" : "mic-outline");
}

function applyChatTranscript(transcript) {
    const input = document.getElementById("chatInput");
    if (!input || !transcript) return;
    input.value = (input.value ? input.value + " " : "") + transcript;
    input.focus();
}

function stopChatMic() {
    if (chatRecognition) {
        try {
            chatRecognition.stop();
        } catch (_) {
            // Ignore if already stopped.
        }
        chatRecognition = null;
    }
    setChatMicState(false);
}

function toggleChatMic() {
    const SR = getSpeechRecognition();
    if (!SR) return;

    if (chatRecognition) {
        stopChatMic();
        return;
    }

    if (chatMicPermission === "denied") {
        console.error("[chat-mic] microphone permission denied");
        flashChatMicHint(tChat("micDenied", "Microphone is blocked. Allow mic access in your browser settings."));
        return;
    }

    const recognition = new SR();
    chatRecognition = recognition;
    let retriedLang = false;
    let captured = "";
    recognition.lang = getSpeechLocale();
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
        captured = Array.from(event.results)
            .map(result => result[0].transcript)
            .join(" ");
    };

    recognition.onend = () => {
        chatRecognition = null;
        setChatMicState(false);
        if (captured) {
            applyChatTranscript(captured);
            captured = "";
        }
    };

    recognition.onerror = (event) => {
        if (!retriedLang && event && event.error === "language-not-supported") {
            retriedLang = true;
            try {
                recognition.lang = "en-US";
                recognition.start();
                return;
            } catch (_) {
                // Fall through to cleanup.
            }
        }
        console.error("[chat-mic] recognition error:", event?.error || event);
        if (event && event.error === "not-allowed") {
            flashChatMicHint(tChat("micDenied", "Microphone is blocked. Allow mic access in your browser settings."));
        }
        chatRecognition = null;
        setChatMicState(false);
    };

    try {
        recognition.start();
        setChatMicState(true);
    } catch (_) {
        console.error("[chat-mic] failed to start:", _);
        chatRecognition = null;
        setChatMicState(false);
    }
}

function closeChatEmojiPicker() {
    const { picker, toggle } = getChatEmojiElements();
    if (picker) picker.hidden = true;
    if (toggle) toggle.setAttribute("aria-expanded", "false");
}

function toggleChatEmojiPicker(event) {
    event?.preventDefault?.();
    event?.stopPropagation?.();

    const { picker, toggle } = getChatEmojiElements();
    if (!picker) return;

    const willOpen = picker.hidden;
    picker.hidden = !willOpen;
    if (toggle) toggle.setAttribute("aria-expanded", willOpen ? "true" : "false");
}

function insertChatEmoji(emoji) {
    const { input } = getChatEmojiElements();
    if (!input) return;

    const value = input.value || "";
    const start = Number.isInteger(input.selectionStart) ? input.selectionStart : value.length;
    const end = Number.isInteger(input.selectionEnd) ? input.selectionEnd : value.length;
    const nextValue = value.slice(0, start) + emoji + value.slice(end);

    input.value = nextValue;
    input.dispatchEvent(new Event("input", { bubbles: true }));

    const nextPos = start + emoji.length;
    try {
        input.setSelectionRange(nextPos, nextPos);
    } catch (_) {
        // Ignore if browser/input type doesn't support selection range.
    }
    input.focus();
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

    if (localStorage.getItem(cacheChatMaximized) === "true") {
        document.getElementById("chatboxModal")?.classList.add("is-maximized");
    }
    syncChatMaximizeToggle();

    if (navigator.permissions && navigator.permissions.query) {
        navigator.permissions.query({ name: "microphone" })
            .then((status) => {
                chatMicPermission = status.state;
                status.addEventListener("change", () => {
                    chatMicPermission = status.state;
                });
            })
            .catch(() => {});
    }

    const chatMicToggle = document.getElementById("chatMicToggle");
    chatMicToggle?.addEventListener("click", toggleChatMic);
    if (chatMicToggle && !getSpeechRecognition()) {
        chatMicToggle.style.display = "none";
    }

    const chatEmojiToggle = document.getElementById("chatEmojiToggle");
    chatEmojiToggle?.addEventListener("click", toggleChatEmojiPicker);

    const chatEmojiPicker = document.getElementById("chatEmojiPicker");
    chatEmojiPicker?.addEventListener("click", (event) => {
        event.stopPropagation();
    });

    document.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof Element)) return;
        if (target.closest(".chatbox-composer-input")) return;
        closeChatEmojiPicker();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeChatEmojiPicker();
    });
};

window.toggleChatbox = toggleChatbox;
window.toggleChatMute = toggleChatMute;
window.toggleChatMaximize = toggleChatMaximize;
window.toggleChatOptions = toggleChatOptions;
window.insertChatEmoji = insertChatEmoji;
window.sendMessage = sendMessage;
window.stopChatResponse = stopChatResponse;
window.clearChat = clearChat;
window.handleChatInputKeydown = handleChatInputKeydown;
