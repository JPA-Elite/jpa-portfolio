// Function to open the image in a modal
function previewImage(imageUrl) {
    var modal = document.getElementById("image-modal");
    var modalImg = document.getElementById("preview-image");

    modal.style.display = "block";
    modalImg.src = imageUrl;
}

// Function to close the modal
function closePreview() {
    var modal = document.getElementById("image-modal");
    modal.style.display = "none";
}

document.addEventListener("DOMContentLoaded", function () {
    let clearBtn = document.getElementById("clear-page-btn");
    let tableBody = document.getElementById("table-body");

    function updateClearButtonState() {
        if (tableBody && tableBody.children.length === 0) {
            clearBtn.disabled = true;
            clearBtn.classList.add("disabled-btn");
        } else {
            clearBtn.disabled = false;
            clearBtn.classList.remove("disabled-btn");
        }
    }

    // Call function on page load to set the correct state
    updateClearButtonState();
    if (clearBtn) {
        clearBtn.addEventListener("click", function () {
            if (confirm("Are you sure you want to clear all data on this page?")) {
                let recordsToDelete = [];

                document.querySelectorAll("#table-body tr").forEach(row => {
                    let recordId = row.dataset.recordId;
                    let imageUrl = row.querySelector(".capture_image")?.src || null;
                    recordsToDelete.push({ _id: recordId, image_capture: imageUrl });
                });

                // Show loading spinner
                showLoading();
                clearBtn.disabled = true;
                clearBtn.innerText = "Clearing...";

                fetch("/api/delete-page-system-info", {
                    method: "DELETE",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ records: recordsToDelete })
                })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        if (data.status === "success") {
                            location.reload();
                        }
                    })
                    .catch(error => console.error("Error:", error))
                    .finally(() => {
                        // Hide spinner and reset button
                        hideLoading();
                        clearBtn.disabled = false;
                        clearBtn.innerText = "Clear Page";
                    });
            }
        });
    }
});