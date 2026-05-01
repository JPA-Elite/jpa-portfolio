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

    const init = () => {
        initThemeToggle();
        initSidebarBehavior();
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init, { once: true });
        return;
    }

    init();
})();
