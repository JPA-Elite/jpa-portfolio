if (!window.__admin_image_preview_modal_loaded__) {
    window.__admin_image_preview_modal_loaded__ = true;

    function isBootstrapModalAvailable() {
        return !!(window.bootstrap && window.bootstrap.Modal);
    }

    function ensureStandaloneCss() {
        if (document.getElementById("ipm-standalone-css")) return;

        const css = `
            #adminImagePreviewModal.ipm-standalone {
                position: fixed;
                inset: 0;
                z-index: 30000;
                display: none;
                align-items: center;
                justify-content: center;
            }
            #adminImagePreviewModal.ipm-standalone.show {
                display: flex;
            }
            #adminImagePreviewModal.ipm-standalone .ipm-backdrop {
                position: absolute;
                inset: 0;
                background: rgba(0, 0, 0, 0.7);
            }
            #adminImagePreviewModal.ipm-standalone .modal-dialog {
                position: relative;
                z-index: 1;
                width: min(960px, 94vw);
                max-height: 92vh;
                background: #1e1e1e;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 18px 50px rgba(0, 0, 0, 0.6);
            }
            #adminImagePreviewModal.ipm-standalone .modal-dialog.modal-fullscreen {
                width: 100vw;
                max-width: 100vw;
                height: 100vh;
                max-height: 100vh;
                border-radius: 0;
            }
            #adminImagePreviewModal.ipm-standalone .modal-content {
                width: 100%;
                max-width: 100%;
                max-height: 100%;
                display: flex;
                flex-direction: column;
            }
            #adminImagePreviewModal.ipm-standalone .modal-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 12px 16px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.12);
            }
            #adminImagePreviewModal.ipm-standalone .modal-title {
                color: #fff;
                font-size: 15px;
                font-weight: 600;
                margin: 0;
            }
            #adminImagePreviewModal.ipm-standalone .preview-header-btn {
                background: transparent;
                border: none;
                color: #fff;
                font-size: 18px;
                line-height: 1;
                cursor: pointer;
                padding: 6px 10px;
                border-radius: 8px;
            }
            #adminImagePreviewModal.ipm-standalone .preview-header-btn:hover {
                background: rgba(255, 255, 255, 0.12);
            }
            #adminImagePreviewModal.ipm-standalone .modal-body {
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 16px;
            }
            #adminImagePreviewModal.ipm-standalone .modal-body img {
                max-width: 100%;
                max-height: 80vh !important;
                object-fit: contain;
                border-radius: 8px;
            }
            #adminImagePreviewModal.ipm-standalone .modal-dialog.modal-fullscreen .modal-body img {
                max-height: calc(100vh - 80px) !important;
            }
            #adminImagePreviewModal.ipm-standalone .bi-arrows-fullscreen::before {
                content: "\\2922";
                font-style: normal;
            }
            #adminImagePreviewModal.ipm-standalone .bi-fullscreen-exit::before {
                content: "\\2921";
                font-style: normal;
            }
            #adminImagePreviewModal.ipm-standalone .bi-x-lg::before {
                content: "\\2715";
                font-style: normal;
            }
            @media (max-width: 768px) {
                #adminImagePreviewModal.ipm-standalone .modal-dialog {
                    width: 96vw;
                    max-width: 96vw;
                    height: 75vh;
                    max-height: 75vh;
                }
                #adminImagePreviewModal.ipm-standalone .modal-dialog.modal-fullscreen {
                    height: 100vh;
                    max-height: 100vh;
                }
                #adminImagePreviewModal.ipm-standalone .modal-body img {
                    max-height: calc(75vh - 80px) !important;
                }
            }
        `;

        const style = document.createElement("style");
        style.id = "ipm-standalone-css";
        style.textContent = css;
        document.head.appendChild(style);
    }

    function showStandalone(modalId) {
        const modalElement = document.getElementById(modalId);
        if (!modalElement) return;
        modalElement.classList.add("show");
        modalElement.setAttribute("aria-hidden", "false");
    }

    function hideStandalone(modalId) {
        const modalElement = document.getElementById(modalId);
        if (!modalElement) return;
        modalElement.classList.remove("show");
        modalElement.setAttribute("aria-hidden", "true");
    }

    window.openAdminImagePreview = function (url, title = "Image Preview") {
        const modalId = "adminImagePreviewModal";
        const standalone = !isBootstrapModalAvailable();

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

            if (standalone) {
                ensureStandaloneCss();
                const modalElement = document.getElementById(modalId);
                modalElement.classList.add("ipm-standalone");

                const backdrop = document.createElement("div");
                backdrop.className = "ipm-backdrop";
                modalElement.insertBefore(backdrop, modalElement.firstChild);

                const closeBtn = modalElement.querySelector('[data-bs-dismiss="modal"]');
                closeBtn.addEventListener("click", function () {
                    hideStandalone(modalId);
                });

                backdrop.addEventListener("click", function () {
                    hideStandalone(modalId);
                });

                document.addEventListener("keydown", function (event) {
                    if (event.key === "Escape" && modalElement.classList.contains("show")) {
                        hideStandalone(modalId);
                    }
                });
            }
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
        if (!modalElement) return;

        if (standalone) {
            showStandalone(modalId);
            return;
        }

        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
        modal.show();
    };
}
