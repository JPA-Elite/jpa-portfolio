/* reusable delete confirmation modal */
(function () {
    if (window.__confirm_delete_modal_loaded__) return;
    window.__confirm_delete_modal_loaded__ = true;

    /**
     * Show the shared delete confirmation modal.
     * @param {string} title - Modal title
     * @param {string} body - Modal body text
     * @param {Function} onConfirm - Called when Delete is confirmed
     */
    window.showDeleteConfirm = function (title, body, onConfirm) {
        const modalEl = document.getElementById("deleteConfirmModal");
        if (!modalEl) return;

        document.getElementById("deleteConfirmModalLabel").textContent = title || "Delete Record";
        document.getElementById("deleteConfirmModalBody").innerHTML = body || "Are you sure you want to delete this record?";

        const confirmBtn = document.getElementById("confirmDeleteBtn");

        /* replace the confirm handler */
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

        newConfirmBtn.addEventListener("click", async function () {
            newConfirmBtn.disabled = true;
            newConfirmBtn.innerHTML = newConfirmBtn.dataset.loadingText || '<span class="spinner-border spinner-border-sm me-2"></span> Deleting...';
            try {
                await onConfirm();
            } finally {
                newConfirmBtn.disabled = false;
                newConfirmBtn.textContent = "Delete";
            }
        });

        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    };

    /* expose a shorthand for simpler cases */
    window.confirmDelete = function (body, onConfirm) {
        window.showDeleteConfirm("Delete Record", body, onConfirm);
    };
})();