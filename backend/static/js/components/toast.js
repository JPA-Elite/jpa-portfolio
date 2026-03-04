(() => {
    if (window.__toast_js_loaded__) return;
    window.__toast_js_loaded__ = true;

    const DEFAULTS = {
        type: "info",
        title: "",
        duration: 3500,
        position: "top-right",
        dismissible: true,
    };

    const ICONS = {
        success: "OK",
        error: "!",
        warning: "!",
        info: "i",
    };

    const getHost = (position) => {
        const selector = `.toast-host[data-position="${position}"]`;
        let host = document.querySelector(selector);
        if (host) return host;

        host = document.createElement("div");
        host.className = "toast-host";
        host.dataset.position = position;
        document.body.appendChild(host);
        return host;
    };

    const buildToast = ({ message, title, type, dismissible }) => {
        const toast = document.createElement("div");
        toast.className = `toast-item toast-${type}`;

        const icon = ICONS[type] || ICONS.info;
        const safeTitle = title ? `<div class="toast-title">${title}</div>` : "";
        const closeBtn = dismissible
            ? `<button class="toast-close" type="button" aria-label="Close">x</button>`
            : "";

        toast.innerHTML = `
            <div class="toast-icon" aria-hidden="true">${icon}</div>
            <div class="toast-body">
                ${safeTitle}
                <div class="toast-message">${message}</div>
            </div>
            ${closeBtn}
        `;

        return toast;
    };

    const removeToast = (toast) => {
        if (!toast) return;
        toast.classList.add("toast-hide");
        toast.addEventListener(
            "animationend",
            () => {
                const host = toast.parentElement;
                toast.remove();
                if (host && !host.children.length) {
                    host.remove();
                }
            },
            { once: true }
        );
    };

    window.showToast = (message, options = {}) => {
        if (!message) return;
        const config = { ...DEFAULTS, ...options, message };
        const host = getHost(config.position);
        const toast = buildToast(config);

        host.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add("toast-show"));

        if (config.dismissible) {
            const closeBtn = toast.querySelector(".toast-close");
            closeBtn?.addEventListener("click", () => removeToast(toast));
        }

        if (config.duration > 0) {
            setTimeout(() => removeToast(toast), config.duration);
        }
    };

    window.notify = (message, type = "info", options = {}) => {
        if (typeof window.showToast === "function") {
            window.showToast(message, { type, ...options });
            return;
        }
        window.alert(message);
    };
})();
