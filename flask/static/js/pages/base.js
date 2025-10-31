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
const currentYear = new Date().getFullYear();
document.getElementById(
    "copyright"
).innerHTML = `&copy; ${currentYear} Joshua Algadipe. All Rights Reserved.`;

function changeLanguage(url) {
    if (typeof window !== "undefined") {
        localStorage.removeItem("chatMessagesCache");
    }

    window.location.href = url;
}

function toggleNav() {
    const sidebar = document.getElementById("sidebar");
    const toggleButton = document.getElementById("toggleButton");
    sidebar.classList.toggle("active");
    toggleButton.classList.toggle("active");
    setTimeout(() => {
        document.body.classList.toggle("nav-active");
    }, 100);
}

// Close sidebar when clicking outside
document.addEventListener("click", function (e) {
    const sidebar = document.getElementById("sidebar");
    const toggle = document.getElementById("toggleButton");
    if (
        !sidebar.contains(e.target) &&
        !toggle.contains(e.target) &&
        sidebar.classList.contains("active")
    ) {
        document.body.classList.remove("nav-active");
        sidebar.classList.remove("active");
        toggle.classList.remove("active");
    }
});

function handleClickOutside(event) {
    const navList = document.getElementById("navList");
    const toggleButton = document.getElementById("toggleButton");

    if (
        navList.classList.contains("show") &&
        !toggleButton.contains(event.target) &&
        !navList.contains(event.target)
    ) {
        document.body.classList.remove("nav-active");
        navList.classList.remove("show");
    }
}

document.body.addEventListener("click", function (event) {
    handleClickOutside(event);
});

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
});

// Handle speech toggle per section
function speak(text, language, button) {
    // If speech is already playing and the same button is clicked, STOP it
    if (currentSpeech && currentButton === button) {
        window.speechSynthesis.cancel();
        currentSpeech = null;
        isSpeaking = false;
        button.classList.remove("active"); // Reset button state
        return;
    }

    // If another button is clicked, stop the current speech
    if (currentSpeech && currentButton !== button) {
        window.speechSynthesis.cancel();
        currentButton.classList.remove("active");
    }

    // Create a new speech instance
    const speech = new SpeechSynthesisUtterance(text);
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
        isSpeaking = false;
        currentSpeech = null;
        button.classList.remove("active"); // Reset button state
    };

    // Automatically stop speech if the user leaves the page
    window.addEventListener("popstate", () => {
        window.speechSynthesis.cancel();
        isSpeaking = false;
        currentSpeech = null;
        if (currentButton) currentButton.classList.remove("active");
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

const observer = new IntersectionObserver(
    (entries, observer) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
                observer.unobserve(entry.target);
            }
        });
    },
    { threshold: 0.2 }
);

sections.forEach((section) => {
    observer.observe(section);
});

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

// Set default theme to dark if no preference is saved
const savedTheme = localStorage.getItem("theme") || "dark";
updateTheme(window.isForceLightMode == "True" ? "light" : savedTheme);

themeToggle.addEventListener("click", () => {
    const currentTheme = root.getAttribute("data-theme");
    const newTheme = currentTheme === "light" ? "dark" : "light";
    updateTheme(newTheme);
    localStorage.setItem("theme", newTheme);
});

document.addEventListener("DOMContentLoaded", function () {
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
