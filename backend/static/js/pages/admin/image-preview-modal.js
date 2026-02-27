if (!window.__admin_image_preview_modal_loaded__) {
    window.__admin_image_preview_modal_loaded__ = true;

    window.openAdminImagePreview = function (url, title = "Image Preview") {
        const modalId = "adminImagePreviewModal";

        if (!document.getElementById(modalId)) {
            const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered modal-xl modal-fullscreen-sm-down">
                    <div class="modal-content bg-dark">
                        <div class="modal-header">
                            <h5 class="modal-title text-white" id="adminImagePreviewTitle">Image Preview</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
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
