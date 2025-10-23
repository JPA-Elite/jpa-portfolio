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
        // Let the CSS handle the brain cells animation background
    } else {
        root.style.setProperty("--bg-opacity", "0.2");
        root.style.setProperty("--bg-color", "rgba(128, 128, 128, 1)");
        root.style.setProperty("--bg-image", `url('${originalBgImage}')`);
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
        const header = document.querySelector("header, .app-header, .navbar-fixed-top");
        const offset = header ? header.offsetHeight : 0;

        function scrollToHash(hash, smooth = true) {
            if (!hash) return;
            const target = document.querySelector(hash);
            if (!target) return;
            const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
            window.scrollTo({ top, behavior: smooth ? "smooth" : "auto" });
        }

        function clearActiveClasses() {
            document.querySelectorAll("li.active").forEach(li => {
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
