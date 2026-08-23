// ---- PAGE LOADING OVERLAY — hide once page is ready ----
(function () {
    var overlay = document.getElementById('pageLoadingOverlay');
    if (!overlay) return;

    // Hide once DOM is ready and all images/fonts have started loading
    function hideOverlay() {
        overlay.classList.add('loaded');
        // Also reveal the admin float button now that page is ready
        document.body.classList.add('loading-done');
        setTimeout(function () {
            overlay.style.display = 'none';
        }, 500);
    }

    // Fallback: always hide after 2s max (prevents stuck loading)
    setTimeout(hideOverlay, 2000);

    // Hide as soon as DOM is built and interactive
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', hideOverlay);
    } else {
        hideOverlay();
    }
})();

// ---- CANVAS NEURAL NETWORK ANIMATION ----
const canvas = document.getElementById("brainCanvas");
const ctx = canvas.getContext("2d");

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

let nodes = [];
const numNodes = window.innerWidth < 600 ? 75 : 150;

function initNodes() {
    nodes = [];
    for (let i = 0; i < numNodes; i++) {
        nodes.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            radius: Math.random() * 3 + 1.5,
            speedX: (Math.random() - 0.5) * 2,
            speedY: (Math.random() - 0.5) * 2,
            flicker: Math.random() < 0.15,
        });
    }
}

function drawConnections() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "limegreen";
    ctx.strokeStyle = "limegreen";
    ctx.lineWidth = 1.2;

    for (let i = 0; i < nodes.length; i++) {
        let nodeA = nodes[i];
        ctx.beginPath();
        ctx.arc(nodeA.x, nodeA.y, nodeA.radius, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < nodes.length; j++) {
            let nodeB = nodes[j];
            let distance = Math.hypot(nodeA.x - nodeB.x, nodeA.y - nodeB.y);
            if (distance < 100) {
                ctx.globalAlpha = 1 - distance / 100;
                ctx.beginPath();
                ctx.moveTo(nodeA.x, nodeA.y);
                ctx.lineTo(nodeB.x, nodeB.y);
                ctx.stroke();
            }
        }
    }
    ctx.globalAlpha = 1;
}

function updateNodes() {
    for (let node of nodes) {
        node.x += node.speedX;
        node.y += node.speedY;
        if (node.x < 0 || node.x > canvas.width) node.speedX *= -1;
        if (node.y < 0 || node.y > canvas.height) node.speedY *= -1;
        if (node.flicker && Math.random() < 0.1) {
            node.x += Math.random() * 6 - 3;
            node.y += Math.random() * 6 - 3;
        }
    }
}

function animateBrain() {
    if (canvas.style.display === "none") return; // stop drawing if hidden
    drawConnections();
    updateNodes();
    requestAnimationFrame(animateBrain);
}

window.addEventListener("resize", resizeCanvas);

// Initialize animation only when dark mode is active
function startBrainAnimation() {
    resizeCanvas();
    initNodes();
    canvas.style.display = "block";
    animateBrain();
}

function stopBrainAnimation() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    canvas.style.display = "none";
}

// Check and apply theme-based display
function handleBrainTheme(theme) {
    if (theme === "dark") {
        startBrainAnimation();
    } else {
        stopBrainAnimation();
    }
}

// Speech Synthesis
let isSpeaking = false; // Track if speech is playing
let currentSpeech = null; // Track the current speech instance
let currentButton = null; // Track the current button being clicked
let currentSpeechHighlight = null; // Track active word highlight state
let speechSessionId = 0; // Ignore stale speech events after switching sections
const currentYear = new Date().getFullYear();
const copyrightEl = document.getElementById("copyright");
if (copyrightEl) {
    const ownerName =
        copyrightEl.dataset.copyrightOwner || "Joshua Algadipe";
    const rightsText =
        copyrightEl.dataset.copyrightRights || "All Rights Reserved.";
    copyrightEl.innerHTML = `&copy; ${currentYear} ${ownerName}. ${rightsText}`;
}

function changeLanguage(url) {
    if (typeof window !== "undefined") {
        localStorage.removeItem("chatMessagesCache");
    }

    window.location.href = url;
}

function toggleNav() {
    var sidebar = document.getElementById("sidebar");
    var toggleButton = document.getElementById("toggleButton");
    var navIcon = toggleButton.querySelector("ion-icon.nav-toggle-icon");
    sidebar.classList.toggle("active");
    toggleButton.classList.toggle("active");

    // Swap hamburger (menu-outline) ↔ close (close-outline) icon with fade animation
    if (navIcon) {
        var isOpen = sidebar.classList.contains("active");
        navIcon.style.transition = "opacity 0.15s ease";
        navIcon.style.opacity = "0";
        setTimeout(function () {
            navIcon.setAttribute("name", isOpen ? "close-outline" : "menu-outline");
            navIcon.style.opacity = "1";
        }, 80);
    }

    setTimeout(function () {
        var isOpen = sidebar.classList.contains("active");
        document.body.classList.toggle("nav-active", isOpen);
        document.body.style.pointerEvents = isOpen ? "none" : "";
        sidebar.style.pointerEvents = "auto";
        toggleButton.style.pointerEvents = "auto";
    }, 100);
}

function toggleMobileMedia(e) {
    e.preventDefault();
    e.stopPropagation();
    const dropdown = document.querySelector(".mobile-media-dropdown");
    if (dropdown) {
        dropdown.classList.toggle("is-open");
    }
}

// Event delegation — catches clicks on .mobile-media-toggle regardless of when it appears in DOM
document.addEventListener("click", function (e) {
    if (e.target.closest(".mobile-media-toggle")) {
        e.preventDefault();
        e.stopPropagation();
        var sidebar = document.getElementById("sidebar");
        var toggleButton = document.getElementById("toggleButton");
        // If sidebar is closed, open it first so the dropdown is visible inside it
        if (!sidebar.classList.contains("active")) {
            sidebar.classList.add("active");
            toggleButton.classList.add("active");
            document.body.classList.add("nav-active");
            document.body.style.pointerEvents = "none";
            sidebar.style.pointerEvents = "auto";
            toggleButton.style.pointerEvents = "auto";
        }
        var dropdown = document.querySelector(".mobile-media-dropdown");
        if (dropdown) {
            dropdown.classList.toggle("is-open");
        }
    }

    // Desktop: toggle media megamenu on click of the trigger
    if (e.target.closest(".media-dropdown-trigger")) {
        e.preventDefault();
        var dropdown = document.querySelector(".media-dropdown");
        if (dropdown) {
            dropdown.classList.toggle("is-open");
        }
    }
});

// Close sidebar and desktop media dropdown when clicking outside
document.addEventListener("click", function (e) {
    const sidebar = document.getElementById("sidebar");
    const toggle = document.getElementById("toggleButton");

    // Don't close sidebar when clicking inside mobile media submenu (Gallery/Vlog/Music links)
    if (e.target.closest(".mobile-media-submenu")) return;

    // Don't close sidebar when clicking the toggle button (it handles its own toggle logic)
    if (e.target.closest(".nav-toggle")) return;

    if (
        !sidebar.contains(e.target) &&
        sidebar.classList.contains("active")
    ) {
        document.body.classList.remove("nav-active");
        sidebar.classList.remove("active");
        toggle.classList.remove("active");
        document.body.style.pointerEvents = "";
        sidebar.style.pointerEvents = "";
        toggle.style.pointerEvents = "";

        // Switch icon back to hamburger
        var navIcon = toggle.querySelector("ion-icon.nav-toggle-icon");
        if (navIcon) {
            navIcon.style.transition = "opacity 0.15s ease";
            navIcon.style.opacity = "0";
            setTimeout(function () {
                navIcon.setAttribute("name", "menu-outline");
                navIcon.style.opacity = "1";
            }, 80);
        }
    }

    // Close desktop media dropdown when clicking outside
    var mediaDropdown = document.querySelector(".media-dropdown");
    if (mediaDropdown && !e.target.closest(".media-dropdown")) {
        mediaDropdown.classList.remove("is-open");
    }
});

// Close sidebar when clicking directly on it (empty area)
var baseSidebar = document.getElementById("sidebar");
if (baseSidebar) {
    baseSidebar.addEventListener("click", function (e) {
        if (e.target === baseSidebar) {
            toggleNav();
        }
    });
}

// Remove old redundant handler — its logic is now merged into the handler above
// (kept here as a no-op placeholder to avoid breaking any external references)

function getVoiceLocale(locale) {
    const voiceMap = {
        en: "en-US",
        ceb: "ceb-PH",
        fr: "fr-FR",
        fil_PH: "tl-PH",
    };

    return voiceMap[locale] || "en-US";
}

// Automatically stop speech when navigating to another page
window.addEventListener("beforeunload", () => {
    window.speechSynthesis.cancel();
    clearSpeechWordHighlight();
});

function clearSpeechWordHighlight() {
    if (!currentSpeechHighlight) return;

    const { container, tokens = [], activeIndex = -1 } = currentSpeechHighlight;
    if (activeIndex >= 0 && tokens[activeIndex]?.el) {
        tokens[activeIndex].el.classList.remove("is-speaking");
    }

    for (let i = tokens.length - 1; i >= 0; i--) {
        const token = tokens[i];
        if (!token?.el || !token.el.parentNode) continue;
        token.el.replaceWith(document.createTextNode(token.el.textContent || ""));
    }

    if (container?.normalize) {
        container.normalize();
    }

    currentSpeechHighlight = null;
}

function createSpeechWordHighlight(container) {
    if (!container) return null;

    clearSpeechWordHighlight();

    const walker = document.createTreeWalker(
        container,
        NodeFilter.SHOW_TEXT,
        {
            acceptNode(node) {
                if (!node || !node.nodeValue) return NodeFilter.FILTER_REJECT;
                if (!node.parentElement) return NodeFilter.FILTER_REJECT;

                const parentTag = node.parentElement.tagName;
                if (parentTag === "SCRIPT" || parentTag === "STYLE") {
                    return NodeFilter.FILTER_REJECT;
                }

                return NodeFilter.FILTER_ACCEPT;
            },
        }
    );

    const textNodes = [];
    let walkerNode = walker.nextNode();
    while (walkerNode) {
        textNodes.push(walkerNode);
        walkerNode = walker.nextNode();
    }

    const tokens = [];
    let globalOffset = 0;

    textNodes.forEach((textNode) => {
        const textValue = textNode.nodeValue || "";
        const wordPattern = /\S+/g;
        let match = wordPattern.exec(textValue);

        if (!match) {
            globalOffset += textValue.length;
            return;
        }

        const fragment = document.createDocumentFragment();
        let lastIndex = 0;

        while (match) {
            const [word] = match;
            const localStart = match.index;
            const localEnd = localStart + word.length;

            if (localStart > lastIndex) {
                fragment.appendChild(document.createTextNode(textValue.slice(lastIndex, localStart)));
            }

            const span = document.createElement("span");
            span.className = "speech-word";
            span.textContent = word;
            fragment.appendChild(span);

            tokens.push({
                el: span,
                start: globalOffset + localStart,
                end: globalOffset + localEnd,
            });

            lastIndex = localEnd;
            match = wordPattern.exec(textValue);
        }

        if (lastIndex < textValue.length) {
            fragment.appendChild(document.createTextNode(textValue.slice(lastIndex)));
        }

        textNode.parentNode.replaceChild(fragment, textNode);
        globalOffset += textValue.length;
    });

    if (!tokens.length) return null;

    currentSpeechHighlight = {
        container,
        tokens,
        activeIndex: -1,
    };

    return currentSpeechHighlight;
}

function updateSpeechWordHighlight(charIndex) {
    if (!currentSpeechHighlight || !Number.isFinite(charIndex)) return;

    const { tokens } = currentSpeechHighlight;
    if (!Array.isArray(tokens) || !tokens.length) return;

    let nextIndex = -1;

    for (let i = 0; i < tokens.length; i++) {
        const token = tokens[i];
        if (charIndex < token.end) {
            nextIndex = i;
            break;
        }
    }

    if (nextIndex < 0) {
        nextIndex = tokens.length - 1;
    }

    if (currentSpeechHighlight.activeIndex === nextIndex) return;

    if (currentSpeechHighlight.activeIndex >= 0) {
        tokens[currentSpeechHighlight.activeIndex]?.el?.classList.remove("is-speaking");
    }

    tokens[nextIndex]?.el?.classList.add("is-speaking");
    currentSpeechHighlight.activeIndex = nextIndex;
}

// Handle speech toggle per section
function speak(text, language, button, highlightTarget = null) {
    // If speech is already playing and the same button is clicked, STOP it
    if (currentSpeech && currentButton === button) {
        speechSessionId++;
        currentSpeech.onend = null;
        currentSpeech.onerror = null;
        currentSpeech.onboundary = null;
        window.speechSynthesis.cancel();
        currentSpeech = null;
        isSpeaking = false;
        button.classList.remove("active"); // Reset button state
        clearSpeechWordHighlight();
        return;
    }

    // If another button is clicked, stop the current speech
    if (currentSpeech && currentButton !== button) {
        speechSessionId++;
        currentSpeech.onend = null;
        currentSpeech.onerror = null;
        currentSpeech.onboundary = null;
        window.speechSynthesis.cancel();
        currentButton.classList.remove("active");
        clearSpeechWordHighlight();
    }

    const highlightContainer =
        typeof highlightTarget === "string"
            ? document.querySelector(highlightTarget)
            : highlightTarget;

    if (highlightContainer) {
        createSpeechWordHighlight(highlightContainer);
    } else {
        clearSpeechWordHighlight();
    }

    // Create a new speech instance
    const speech = new SpeechSynthesisUtterance(text);
    const activeSpeechSessionId = ++speechSessionId;
    const voices = window.speechSynthesis.getVoices();

    // Find a male voice based on language
    const maleVoice = voices.find(
        (voice) =>
            voice.lang === language &&
            (voice.name.toLowerCase().includes("male") || voice.gender === "male")
    );

    // Set male voice if found, otherwise default to the language
    if (maleVoice) {
        speech.voice = maleVoice;
    } else {
        speech.lang = language;
    }

    // Set speech properties
    speech.pitch = 1;
    speech.rate = 1;
    speech.volume = 1;

    // Track the current speech and button
    currentSpeech = speech;
    currentButton = button;
    isSpeaking = true;
    button.classList.add("active"); // Add active state to button

    // Automatically detect when the speech ends
    speech.onend = () => {
        if (currentSpeech !== speech || speechSessionId !== activeSpeechSessionId) return;
        isSpeaking = false;
        currentSpeech = null;
        button.classList.remove("active"); // Reset button state
        clearSpeechWordHighlight();
    };

    speech.onerror = () => {
        if (currentSpeech !== speech || speechSessionId !== activeSpeechSessionId) return;
        isSpeaking = false;
        currentSpeech = null;
        button.classList.remove("active");
        clearSpeechWordHighlight();
    };

    speech.onboundary = (event) => {
        if (currentSpeech !== speech || speechSessionId !== activeSpeechSessionId) return;
        if (typeof event?.charIndex !== "number") return;
        updateSpeechWordHighlight(event.charIndex);
    };

    // Automatically stop speech if the user leaves the page
    window.addEventListener("popstate", () => {
        window.speechSynthesis.cancel();
        isSpeaking = false;
        currentSpeech = null;
        if (currentButton) currentButton.classList.remove("active");
        clearSpeechWordHighlight();
    });

    // Start the speech immediately
    window.speechSynthesis.speak(speech);
}

window.addEventListener("scroll", function () {
    const header = document.querySelector("header");

    // if (window.innerWidth > 768) {
    if (window.scrollY > 10) {
        header.classList.add("header-scrolled");
    } else {
        header.classList.remove("header-scrolled");
    }
    // } else {
    //     header.classList.remove("header-scrolled");
    // }
});

const sections = document.querySelectorAll("section");

if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
        (entries, observer) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                    observer.unobserve(entry.target);
                }
            });
        },
        {
            // Use a low threshold so tall sections (e.g. gallery on mobile)
            // still become visible even when only a small part is in view.
            threshold: 0.01,
        }
    );

    sections.forEach((section) => {
        observer.observe(section);
    });
} else {
    // Fallback for older/mobile browsers without IntersectionObserver.
    sections.forEach((section) => {
        section.classList.add("visible");
    });
}

// Theme switching functionality
const themeToggle = document.getElementById("themeToggle");
const root = document.documentElement;

function updateTheme(theme) {
    root.setAttribute("data-theme", theme);

    const originalBgImage = window.backgroundImageUrl;

    if (theme === "dark") {
        root.style.setProperty("--bg-opacity", "0.1");
        root.style.setProperty("--bg-color", "rgba(0, 0, 0, 0.95)");
        handleBrainTheme("dark");
    } else {
        root.style.setProperty("--bg-opacity", "0.2");
        root.style.setProperty("--bg-color", "rgba(128, 128, 128, 1)");
        root.style.setProperty("--bg-image", `url('${originalBgImage}')`);
        handleBrainTheme("light");
    }
}

// Set default theme to light if no preference is saved
const savedTheme = localStorage.getItem("theme") || "light";
updateTheme(window.isForceLightMode == "True" ? "light" : savedTheme);

// ── Lazy Reveal ──────────────────────────────────────────────────────────────
// Reusable: sections/elements fade + slide in when scrolled into view.
function setupLazyReveal() {
    const els = document.querySelectorAll(".lazy-reveal");
    if (!els.length) return;

    els.forEach((el) => el.classList.add("lazy-pending"));

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-revealed");
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.08, rootMargin: "0px 0px 40px 0px" }
    );

    els.forEach((el) => observer.observe(el));
}

themeToggle.addEventListener("click", () => {
    const currentTheme = root.getAttribute("data-theme");
    const newTheme = currentTheme === "light" ? "dark" : "light";
    updateTheme(newTheme);
    localStorage.setItem("theme", newTheme);
});

function setupAdminFloatToggle() {
    const wrap = document.getElementById("adminFloat");
    const toggle = wrap ? wrap.querySelector(".admin-float-toggle") : null;
    if (!wrap || !toggle) return;
    toggle.addEventListener("click", () => {
        const maximized = wrap.classList.toggle("is-maximized");
        toggle.setAttribute("aria-expanded", String(maximized));
        toggle.setAttribute(
            "aria-label",
            maximized ? "Minimize Admin Panel" : "Maximize Admin Panel"
        );
    });
}

document.addEventListener("DOMContentLoaded", function () {
    setupLazyReveal();
    setupAdminFloatToggle();

    if (window.isProfessionalMode) {
        const header = document.querySelector(
            "header, .app-header, .navbar-fixed-top"
        );
        const offset = header ? header.offsetHeight : 0;

        function scrollToHash(hash, smooth = true) {
            if (!hash) return;
            const target = document.querySelector(hash);
            if (!target) return;
            const top =
                target.getBoundingClientRect().top + window.pageYOffset - offset;
            window.scrollTo({ top, behavior: smooth ? "smooth" : "auto" });
        }

        function clearActiveClasses() {
            document.querySelectorAll("li.active").forEach((li) => {
                li.classList.remove("active");
            });
        }

        function activateLinkByHash(hash) {
            if (!hash) return;
            clearActiveClasses();
            const activeLink = document.querySelector(`a[href$="${hash}"]`);
            if (activeLink && activeLink.parentElement) {
                activeLink.parentElement.classList.add("active");
            }
        }

        document.querySelectorAll('a[href*="#"]').forEach(function (anchor) {
            const url = new URL(anchor.href, window.location.origin);
            const hash = url.hash;

            anchor.addEventListener("click", function (e) {
                if (url.pathname === window.location.pathname && hash) {
                    e.preventDefault();
                    activateLinkByHash(hash);
                    scrollToHash(hash, true);
                    history.pushState(null, "", url.pathname + url.search + hash);
                }
            });
        });

        const initialHash = window.location.hash;
        if (initialHash) {
            activateLinkByHash(initialHash);
            setTimeout(() => scrollToHash(initialHash, false), 50);
        }
    }
});
