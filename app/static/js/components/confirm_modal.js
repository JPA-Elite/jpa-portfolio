(function () {
    if (window.__confirmModalLoaded) return;
    window.__confirmModalLoaded = true;

    let _onConfirm = null;

    function openConfirmModal({ title, message, confirmText, onConfirm } = {}) {
        const modal = document.getElementById("confirmModal");
        if (!modal) return;

        const titleEl = document.getElementById("confirmModalTitle");
        const bodyEl = document.getElementById("confirmModalBody");
        const confirmBtn = document.getElementById("confirmModalConfirmBtn");

        if (titleEl) titleEl.textContent = title || "Confirm";
        if (bodyEl) bodyEl.textContent = message || "Are you sure?";
        if (confirmBtn) confirmBtn.textContent = confirmText || "Confirm";

        _onConfirm = typeof onConfirm === "function" ? onConfirm : null;

        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("confirm-modal-open");
    }

    function closeConfirmModal() {
        const modal = document.getElementById("confirmModal");
        if (!modal) return;
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("confirm-modal-open");
        const confirmBtn = document.getElementById("confirmModalConfirmBtn");
        if (confirmBtn) setButtonLoading(confirmBtn, false);
        _onConfirm = null;
    }

    function setButtonLoading(btn, loading) {
        if (!btn) return;
        if (loading) {
            if (!btn.dataset.originalText) {
                btn.dataset.originalText = btn.textContent || "";
            }
            btn.textContent = "";
            btn.classList.add("is-loading");
            btn.setAttribute("aria-busy", "true");
            btn.disabled = true;
        } else {
            if (btn.dataset.originalText) {
                btn.textContent = btn.dataset.originalText;
                delete btn.dataset.originalText;
            }
            btn.classList.remove("is-loading");
            btn.removeAttribute("aria-busy");
            btn.disabled = false;
        }
    }

    document.addEventListener("click", function (e) {
        const modal = document.getElementById("confirmModal");
        if (!modal || !modal.classList.contains("is-open")) return;

        if (e.target.closest("[data-confirm-close]")) {
            if (modal.querySelector("#confirmModalConfirmBtn.is-loading")) return;
            closeConfirmModal();
            return;
        }

        const confirmBtn = e.target.closest("#confirmModalConfirmBtn");
        if (confirmBtn) {
            const fn = _onConfirm;
            if (typeof fn !== "function") {
                closeConfirmModal();
                return;
            }
            setButtonLoading(confirmBtn, true);
            Promise.resolve(fn()).finally(() => {
                closeConfirmModal();
            });
        }
    });

    window.openConfirmModal = openConfirmModal;
    window.closeConfirmModal = closeConfirmModal;
})();
