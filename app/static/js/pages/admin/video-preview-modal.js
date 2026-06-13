if (!window.__admin_video_preview_modal_loaded__) {
    window.__admin_video_preview_modal_loaded__ = true;

    window.playVideoPreview = function (url) {
        const modalId = "videoPreviewModal";

        if (!document.getElementById(modalId)) {
            const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered modal-xl modal-fullscreen-sm-down" id="videoPreviewDialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title me-auto">Video Preview</h5>
                            <div class="d-flex align-items-center gap-1">
                                <button type="button" class="btn p-1 preview-header-btn" id="videoMaximizeBtn" aria-label="Maximize" title="Maximize">
                                    <i class="bi bi-arrows-fullscreen"></i>
                                </button>
                                <button type="button" class="btn p-1 preview-header-btn" data-bs-dismiss="modal" aria-label="Close">
                                    <i class="bi bi-x-lg"></i>
                                </button>
                            </div>
                        </div>
                        <div class="modal-body text-center">
                            <video id="previewPlayer" class="w-100" controls preload="auto" style="max-height:70vh;">
                                <source id="previewSource" src="" type="video/mp4">
                                Your browser does not support the video tag.
                            </video>
                        </div>
                    </div>
                </div>
            </div>`;
            document.body.insertAdjacentHTML("beforeend", modalHtml);

            // Maximize / minimize toggle
            const maxBtn = document.getElementById("videoMaximizeBtn");
            const dialog = document.getElementById("videoPreviewDialog");
            const player = document.getElementById("previewPlayer");
            maxBtn.addEventListener("click", function () {
                dialog.classList.toggle("modal-fullscreen");
                const isFull = dialog.classList.contains("modal-fullscreen");
                if (player) {
                    player.style.maxHeight = isFull ? "100vh" : "70vh";
                }
                maxBtn.innerHTML = isFull
                    ? '<i class="bi bi-fullscreen-exit"></i>'
                    : '<i class="bi bi-arrows-fullscreen"></i>';
                maxBtn.setAttribute("title", isFull ? "Restore" : "Maximize");
                maxBtn.setAttribute("aria-label", isFull ? "Restore" : "Maximize");
            });

            // Stop video when modal closes
            document.getElementById(modalId).addEventListener("hidden.bs.modal", () => {
                const p = document.getElementById("previewPlayer");
                p.pause();
                p.currentTime = 0;
            });

            // Autoplay video when modal opens
            document.getElementById(modalId).addEventListener("shown.bs.modal", () => {
                const p = document.getElementById("previewPlayer");
                p.play().catch(err => {
                    console.warn("Autoplay blocked by browser:", err);
                });
            });
        }

        document.getElementById("previewSource").src = url;
        const player = document.getElementById("previewPlayer");
        player.load();

        const modal = new bootstrap.Modal(document.getElementById(modalId));
        modal.show();
    };
}