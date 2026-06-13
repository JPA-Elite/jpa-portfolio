if (!window.__admin_image_preview_modal_loaded__) {
    window.__admin_image_preview_modal_loaded__ = true;

    window.openAdminImagePreview = function (url, title = "Image Preview") {
        const modalId = "adminImagePreviewModal";

        if (!document.getElementById(modalId)) {
            const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered modal-xl modal-fullscreen-sm-down">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title me-auto" id="adminImagePreviewTitle">Image Preview</h5>
                            <div class="d-flex align-items-center gap-1">
                                <button type="button" class="btn p-1 preview-header-btn" id="adminImageMaximizeBtn" aria-label="Maximize" title="Maximize">
                                    <i class="bi bi-arrows-fullscreen"></i>
                                </button>
                                <button type="button" class="btn p-1 preview-header-btn" data-bs-dismiss="modal" aria-label="Close">
                                    <i class="bi bi-x-lg"></i>
                                </button>
                            </div>
                        </div>
                        <div class="modal-body d-flex justify-content-center align-items-center">
                            <img id="adminImagePreviewSource"
                                class="img-fluid rounded shadow"
                                style="max-width:100%; max-height:80vh; object-fit:contain;" />
                        </div>
                    </div>
                </div>
            </div>`;
            document.body.insertAdjacentHTML("beforeend", modalHtml);

            // Maximize / minimize toggle
            const maxBtn = document.getElementById("adminImageMaximizeBtn");
            const dialog = document.querySelector("#" + modalId + " .modal-dialog");
            const previewImg = document.getElementById("adminImagePreviewSource");
            maxBtn.addEventListener("click", function () {
                dialog.classList.toggle("modal-fullscreen");
                const isFull = dialog.classList.contains("modal-fullscreen");
                if (previewImg) {
                    previewImg.style.maxHeight = isFull ? "100vh" : "80vh";
                }
                maxBtn.innerHTML = isFull
                    ? '<i class="bi bi-fullscreen-exit"></i>'
                    : '<i class="bi bi-arrows-fullscreen"></i>';
                maxBtn.setAttribute("title", isFull ? "Restore" : "Maximize");
                maxBtn.setAttribute("aria-label", isFull ? "Restore" : "Maximize");
            });
        }

        const previewImg = document.getElementById("adminImagePreviewSource");
        const previewTitle = document.getElementById("adminImagePreviewTitle");
        if (!previewImg) return;

        previewImg.src = url || "";
        previewImg.alt = title || "Image Preview";
        if (previewTitle) {
            previewTitle.textContent = title || "Image Preview";
        }

        const modalElement = document.getElementById(modalId);
        if (!modalElement || !window.bootstrap?.Modal) return;

        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
        modal.show();
    };
}
