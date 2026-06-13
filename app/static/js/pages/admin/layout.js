(() => {
    "use strict";

    const THEME_STORAGE_KEY = "admin.theme";
    const SIDEBAR_STORAGE_KEY = "admin.sidebar.collapsed";
    const MOBILE_BREAKPOINT = 992;

    const body = document.body;
    const root = document.documentElement;
    const sidebar = document.getElementById("adminSidebar");
    const themeToggle = document.getElementById("adminThemeToggle");
    const sidebarToggleButtons = document.querySelectorAll('[data-lte-toggle="sidebar"]');
    const sidebarCollapseButton = document.getElementById("sidebarCollapseButton");
    const sidebarCollapseIcon = document.getElementById("sidebarCollapseIcon");
    const sidebarCollapseLabel = document.getElementById("sidebarCollapseLabel");
    const sidebarNavLinks = document.querySelectorAll("#navigation .nav-link");

    const readStorage = (key) => {
        try {
            return window.localStorage.getItem(key);
        } catch {
            return null;
        }
    };

    const writeStorage = (key, value) => {
        try {
            window.localStorage.setItem(key, value);
        } catch {
            // Ignore storage issues in restricted environments.
        }
    };

    const isMobileView = () => window.innerWidth < MOBILE_BREAKPOINT;
    const isSidebarCollapsed = () => body.classList.contains("sidebar-collapse");

    const getPreferredTheme = () => {
        const storedTheme = readStorage(THEME_STORAGE_KEY);
        if (storedTheme === "light" || storedTheme === "dark") {
            return storedTheme;
        }

        const prefersDark = window.matchMedia &&
            window.matchMedia("(prefers-color-scheme: dark)").matches;
        return prefersDark ? "dark" : "light";
    };

    const applyTheme = (theme) => {
        const activeTheme = theme === "dark" ? "dark" : "light";
        root.setAttribute("data-bs-theme", activeTheme);

        if (sidebar) {
            sidebar.setAttribute("data-bs-theme", activeTheme);
        }
    };

    const applySidebarStateForViewport = () => {
        if (isMobileView()) {
            body.classList.remove("sidebar-open");
            body.classList.add("sidebar-collapse");
            return;
        }

        const storedCollapsed = readStorage(SIDEBAR_STORAGE_KEY) === "true";
        body.classList.toggle("sidebar-collapse", storedCollapsed);
        body.classList.toggle("sidebar-open", !storedCollapsed);
    };

    const persistSidebarState = () => {
        if (isMobileView()) {
            return;
        }

        writeStorage(SIDEBAR_STORAGE_KEY, String(isSidebarCollapsed()));
    };

    const updateSidebarCollapseControl = () => {
        if (!sidebarCollapseButton || !sidebarCollapseIcon || !sidebarCollapseLabel) {
            return;
        }

        const isMobile = isMobileView();
        const isOpen = body.classList.contains("sidebar-open") && !isSidebarCollapsed();
        sidebarCollapseIcon.className = "bi";

        if (isMobile) {
            if (isOpen) {
                sidebarCollapseIcon.classList.add("bi-x-lg");
                sidebarCollapseLabel.textContent = "Close Menu";
                sidebarCollapseButton.setAttribute("aria-label", "Close sidebar menu");
            } else {
                sidebarCollapseIcon.classList.add("bi-list");
                sidebarCollapseLabel.textContent = "Open Menu";
                sidebarCollapseButton.setAttribute("aria-label", "Open sidebar menu");
            }
            return;
        }

        if (isSidebarCollapsed()) {
            sidebarCollapseIcon.classList.add("bi-layout-sidebar");
            sidebarCollapseLabel.textContent = "Expand Sidebar";
            sidebarCollapseButton.setAttribute("aria-label", "Expand sidebar");
            return;
        }

        sidebarCollapseIcon.classList.add("bi-layout-sidebar-inset");
        sidebarCollapseLabel.textContent = "Collapse Sidebar";
        sidebarCollapseButton.setAttribute("aria-label", "Collapse sidebar");
    };

    const closeSidebarOnMobileNavClick = () => {
        if (!isMobileView()) {
            return;
        }

        body.classList.remove("sidebar-open");
        body.classList.add("sidebar-collapse");
        updateSidebarCollapseControl();
    };

    const initThemeToggle = () => {
        const preferredTheme = getPreferredTheme();
        applyTheme(preferredTheme);

        // Sync checkbox state: checked = dark, unchecked = light
        if (themeToggle) {
            themeToggle.checked = preferredTheme === "dark";
        }

        if (!themeToggle) {
            return;
        }

        themeToggle.addEventListener("change", () => {
            const nextTheme = themeToggle.checked ? "dark" : "light";
            applyTheme(nextTheme);
            writeStorage(THEME_STORAGE_KEY, nextTheme);
        });
    };

    const initSidebarBehavior = () => {
        applySidebarStateForViewport();
        updateSidebarCollapseControl();

        sidebarToggleButtons.forEach((toggleButton) => {
            toggleButton.addEventListener("click", () => {
                window.setTimeout(() => {
                    persistSidebarState();
                    updateSidebarCollapseControl();
                }, 20);
            });
        });

        sidebarNavLinks.forEach((link) => {
            link.addEventListener("click", closeSidebarOnMobileNavClick);
        });

        const classObserver = new MutationObserver(() => {
            updateSidebarCollapseControl();
        });
        classObserver.observe(body, { attributes: true, attributeFilter: ["class"] });

        let wasMobile = isMobileView();
        window.addEventListener("resize", () => {
            const isMobile = isMobileView();
            if (isMobile !== wasMobile) {
                applySidebarStateForViewport();
                wasMobile = isMobile;
            }
            updateSidebarCollapseControl();
        });
    };

    const initMiniCollapseSidebarTooltips = () => {
        const links = document.querySelectorAll('#navigation .nav-link[data-sidebar-tooltip]');
        if (!links.length) return;

        const styleId = "adminMiniSidebarTooltipStyle";
        if (!document.getElementById(styleId)) {
            const styleEl = document.createElement("style");
            styleEl.id = styleId;
            styleEl.textContent = `
#adminMiniSidebarTooltip{
  position:fixed;
  z-index:100000;
  background:rgba(17,24,39,0.98);
  color:#fff;
  border-radius:10px;
  padding:10px 12px;
  font-size:13px;
  line-height:1;
  font-weight:600;
  white-space:nowrap;
  pointer-events:none;
  transform:translateY(-50%);
  box-shadow:0 10px 30px rgba(0,0,0,0.25);
}
#adminMiniSidebarTooltip::before{
  content:"";
  position:absolute;
  top:50%;
  left:-8px;
  transform:translateY(-50%);
  width:0;height:0;
  border-top:8px solid transparent;
  border-bottom:8px solid transparent;
  border-right:8px solid rgba(17,24,39,0.98);
}
#adminMiniSidebarTooltip[data-bs-theme="dark"]{
  background:rgba(17,24,39,0.98);
}
#adminMiniSidebarTooltip[data-bs-theme="dark"]::before{
  border-right-color: rgba(17,24,39,0.98);
}
`;
            document.head.appendChild(styleEl);
        }

        const tooltipEl = document.createElement("div");
        tooltipEl.id = "adminMiniSidebarTooltip";
        tooltipEl.setAttribute("role", "tooltip");
        tooltipEl.style.display = "none";
        document.body.appendChild(tooltipEl);

        const isMiniCollapsedDesktop = () =>
            !isMobileView() &&
            body.classList.contains("sidebar-mini") &&
            body.classList.contains("sidebar-collapse");

        const positionTooltip = (linkEl) => {
            const rect = linkEl.getBoundingClientRect();
            const centerY = rect.top + rect.height / 2;

            tooltipEl.style.left = `${rect.right + 12}px`;
            tooltipEl.style.top = `${centerY}px`;
        };

        const showTooltip = (linkEl) => {
            if (!isMiniCollapsedDesktop()) return;

            const text = linkEl.getAttribute("data-sidebar-tooltip") || "";
            if (!text) return;

            const theme = root.getAttribute("data-bs-theme") || "light";
            tooltipEl.setAttribute("data-bs-theme", theme);

            tooltipEl.textContent = text;
            tooltipEl.style.display = "block";
            positionTooltip(linkEl);
        };

        const hideTooltip = () => {
            tooltipEl.style.display = "none";
        };

        links.forEach((linkEl) => {
            linkEl.addEventListener("mouseenter", () => showTooltip(linkEl));
            linkEl.addEventListener("mouseleave", hideTooltip);

            linkEl.addEventListener("focus", () => showTooltip(linkEl));
            linkEl.addEventListener("blur", hideTooltip);
        });

        window.addEventListener("scroll", hideTooltip, { passive: true });
        window.addEventListener("resize", hideTooltip);

        // Hide tooltip when the sidebar state changes
        const obs = new MutationObserver(() => {
            if (!isMiniCollapsedDesktop()) hideTooltip();
        });
        obs.observe(body, { attributes: true, attributeFilter: ["class"] });
    };

    const initFlashToasts = () => {
        const toasts = document.querySelectorAll(".flash-toast");
        toasts.forEach((toast) => {
            setTimeout(() => {
                toast.classList.add("fade-out");
                toast.addEventListener("animationend", () => toast.remove(), { once: true });
            }, 4000);
        });
    };

    const init = () => {
        initThemeToggle();
        initSidebarBehavior();
        initMiniCollapseSidebarTooltips();
        initFlashToasts();
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, { once: true });
        return;
    }

    init();
})();
