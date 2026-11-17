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
const prefersReducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const numNodes = prefersReducedMotion ? 0 : (window.innerWidth < 480 ? 40 : (window.innerWidth < 900 ? 60 : 90));
let brainAnimationId = 0;
let brainRunning = false;

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
            let dx = nodeA.x - nodeB.x;
            let dy = nodeA.y - nodeB.y;
            let distSq = dx * dx + dy * dy;
            if (distSq < 10000) {
                let distance = Math.sqrt(distSq);
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
    if (!brainRunning) return;
    if (canvas.style.display === "none" || document.hidden) {
        brainAnimationId = requestAnimationFrame(animateBrain);
        return;
    }
    drawConnections();
    updateNodes();
    brainAnimationId = requestAnimationFrame(animateBrain);
}

function startBrainAnimation() {
    if (prefersReducedMotion || numNodes === 0) {
        canvas.style.display = "none";
        return;
    }
    resizeCanvas();
    initNodes();
    canvas.style.display = "block";
    if (!brainRunning) {
        brainRunning = true;
        animateBrain();
    }
}

function stopBrainAnimation() {
    brainRunning = false;
    if (brainAnimationId) {
        cancelAnimationFrame(brainAnimationId);
        brainAnimationId = 0;
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    canvas.style.display = "none";
}

window.addEventListener("resize", function () {
    if (brainRunning) {
        resizeCanvas();
    }
});

// Check and apply theme-based display
function handleBrainTheme(theme) {
    if (theme === "dark") {
        startBrainAnimation();
    } else {
        stopBrainAnimation();
    }
}

const copyrightEl = document.getElementById("copyright");
if (copyrightEl) {
    const ownerName =
        copyrightEl.dataset.copyrightOwner || "Joshua Algadipe";
    const rightsText =
        copyrightEl.dataset.copyrightRights || "All Rights Reserved.";
    copyrightEl.innerHTML = `&copy; 2025 ${ownerName}. ${rightsText}`;
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
            document.querySelectorAll(`a[href$="${hash}"]`).forEach((activeLink) => {
                const parent = activeLink && activeLink.parentElement;
                if (parent && parent.tagName === "LI") {
                    parent.classList.add("active");
                }
            });
            positionSpyByHash(hash);
        }

        var isProHost = window.isProfessionalMode === "True";
        var desktopSpyQuery = window.matchMedia ? window.matchMedia("(min-width: 769px)") : null;

        function spyEl() {
            if (!isProHost) return null;
            var list = document.getElementById("navList");
            if (!list) return null;
            var el = list.querySelector(".nav-spy");
            if (!el) {
                el = document.createElement("span");
                el.className = "nav-spy";
                el.setAttribute("aria-hidden", "true");
                list.appendChild(el);
            }
            return el;
        }

        function spyLinkX(link, list) {
            var x = 0;
            var el = link;
            while (el && el !== list) {
                x += el.offsetLeft || 0;
                el = el.offsetParent;
            }
            return x;
        }

        function positionSpyByHash(hash) {
            var el = spyEl();
            if (!el) return;
            if (!desktopSpyQuery || !desktopSpyQuery.matches) {
                el.style.opacity = "0";
                return;
            }
            var list = document.getElementById("navList");
            var link = list ? list.querySelector('a[href$="' + hash + '"]') : null;
            if (!link) {
                el.style.opacity = "0";
                return;
            }
            el.style.opacity = "1";
            el.style.width = link.offsetWidth + "px";
            el.style.transform = "translateX(" + spyLinkX(link, list) + "px)";
        }

        if (isProHost) {
            var spySectionIds = [];
            document.querySelectorAll('#navList a[href*="#"]').forEach(function (anchor) {
                var parts = (anchor.getAttribute("href") || "").split("#");
                var id = parts[1];
                if (id && document.getElementById(id) && spySectionIds.indexOf(id) === -1) {
                    spySectionIds.push(id);
                }
            });
            var lastSpyId = null;
            var spyLockedId = null;
            var spyLockTimer = null;
            function lockSpy(id) {
                spyLockedId = id;
                if (spyLockTimer) window.clearTimeout(spyLockTimer);
                spyLockTimer = window.setTimeout(function () {
                    spyLockedId = null;
                    spyLockTimer = null;
                    lastSpyId = id;
                }, 900);
            }
            function spyHeaderOffset() {
                var bar = document.querySelector("header");
                return (bar ? bar.offsetHeight : 0) + 8;
            }
            function spySectionFromScroll() {
                var line = window.pageYOffset + spyHeaderOffset() + window.innerHeight * 0.25;
                var current = null;
                spySectionIds.forEach(function (id) {
                    var section = document.getElementById(id);
                    if (section && section.getBoundingClientRect().top + window.pageYOffset <= line) {
                        current = id;
                    }
                });
                return current;
            }
            var spyTicking = false;
            function spyOnScroll() {
                if (spyTicking) return;
                spyTicking = true;
                window.requestAnimationFrame(function () {
                    spyTicking = false;
                    if (spyLockedId) return;
                    var id = spySectionFromScroll();
                    if (id && id !== lastSpyId) {
                        lastSpyId = id;
                        activateLinkByHash("#" + id);
                        positionSpyByHash("#" + id);
                    }
                });
            }
            if (spySectionIds.length) {
                window.addEventListener("scroll", spyOnScroll, { passive: true });
                window.addEventListener("resize", function () {
                    lastSpyId = null;
                    spyOnScroll();
                });
                window.addEventListener("load", function () {
                    lastSpyId = null;
                    spyOnScroll();
                });
                if (document.fonts && document.fonts.ready) {
                    document.fonts.ready.then(function () {
                        lastSpyId = null;
                        spyOnScroll();
                    });
                }
                spyOnScroll();
            }
        }

        document.querySelectorAll('a[href*="#"]').forEach(function (anchor) {
            const url = new URL(anchor.href, window.location.origin);
            const hash = url.hash;

            anchor.addEventListener("click", function (e) {
                if (url.pathname === window.location.pathname && hash) {
                    e.preventDefault();
                    activateLinkByHash(hash);
                    if (isProHost && typeof lockSpy === "function") {
                        lockSpy(hash.replace("#", ""));
                    }
                    scrollToHash(hash, true);
                    history.pushState(null, "", url.pathname + url.search + hash);
                    var sidebar = document.getElementById("sidebar");
                    if (sidebar && sidebar.classList.contains("active") && typeof toggleNav === "function") {
                        toggleNav();
                    }
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
