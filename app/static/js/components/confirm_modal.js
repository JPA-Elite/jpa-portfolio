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
        _onConfirm = null;
    }

    document.addEventListener("click", function (e) {
        const modal = document.getElementById("confirmModal");
        if (!modal || !modal.classList.contains("is-open")) return;

        if (e.target.closest("[data-confirm-close]")) {
            closeConfirmModal();
            return;
        }

        const confirmBtn = e.target.closest("#confirmModalConfirmBtn");
        if (confirmBtn) {
            const fn = _onConfirm;
            _onConfirm = null;
            closeConfirmModal();
            if (typeof fn === "function") fn();
        }
    });

    window.openConfirmModal = openConfirmModal;
    window.closeConfirmModal = closeConfirmModal;
})();
