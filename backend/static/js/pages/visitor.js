// Function to open the image in a modal
function previewImage(imageUrl) {
    const modal = document.getElementById("image-modal");
    const modalImg = document.getElementById("preview-image");

    if (!modal || !modalImg) return;

    modal.style.display = "block";
    modalImg.src = imageUrl;
}

// Function to close the modal
function closePreview() {
    const modal = document.getElementById("image-modal");
    if (!modal) return;

    modal.style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
    const clearBtn = document.getElementById("clear-page-btn");
    const tableBody = document.getElementById("table-body");

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

    async function clearPageSystemInfo() {
        const records = Array.from(document.querySelectorAll("#table-body tr")).map((row) => ({
            _id: row.dataset.recordId,
            image_capture: row.querySelector(".capture_image")?.src || null,
        }));

        const response = await fetch("/api/delete-page-system-info", {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ records }),
        });

        if (!response.ok) {
            throw new Error("Failed to clear page system info");
        }

        return response.json();
    }

    updateClearButtonState();

    if (!clearBtn) return;

    clearBtn.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to clear all data on this page?")) {
            return;
        }

        showLoading();
        setClearButtonLoading(true);

        try {
            const data = await clearPageSystemInfo();
            alert(data.message);

            if (data.status === "success") {
                location.reload();
            }
        } catch (error) {
            console.error("Error:", error);
        } finally {
            hideLoading();
            setClearButtonLoading(false);
        }
    });
});
