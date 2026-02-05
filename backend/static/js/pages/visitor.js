import { SystemInfoService } from "../services/SystemInfoService.js";

function previewImage(imageUrl) {
    const modal = document.getElementById("image-modal");
    const modalImg = document.getElementById("preview-image");

    if (!modal || !modalImg) return;

    modal.style.display = "block";
    modalImg.src = imageUrl;
}

function closePreview() {
    const modal = document.getElementById("image-modal");
    if (!modal) return;

    modal.style.display = "none";
}

window.previewImage = previewImage;
window.closePreview = closePreview;

document.addEventListener("DOMContentLoaded", () => {
    const clearBtn = document.getElementById("clear-page-btn");
    const tableBody = document.getElementById("table-body");
    const systemInfoService = new SystemInfoService();

    function updateClearButtonState() {
        if (!clearBtn) return;

        const hasNoRows = tableBody?.children.length === 0;
        clearBtn.disabled = hasNoRows;
        clearBtn.classList.toggle("disabled-btn", hasNoRows);
    }

    function setClearButtonLoading(isLoading) {
        if (!clearBtn) return;

        clearBtn.disabled = isLoading;
        clearBtn.innerText = isLoading ? "Clearing..." : "Clear Page";
    }

    function getRecordsToDelete() {
        return Array.from(document.querySelectorAll("#table-body tr")).map((row) => ({
            _id: row.dataset.recordId,
            image_capture: row.querySelector(".capture_image")?.src || null,
        }));
    }

    updateClearButtonState();

    if (!clearBtn) return;

    clearBtn.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to clear all data on this page?")) return;

        showLoading();
        setClearButtonLoading(true);

        try {
            const records = getRecordsToDelete();
            const data = await systemInfoService.clearPageSystemInfo(records);
            alert(data.message);

            if (data.status === "success") {
                location.reload();
            }
        } finally {
            hideLoading();
            setClearButtonLoading(false);
        }
    });
});
