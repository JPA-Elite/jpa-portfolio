import { AdminCrudService } from "../../services/AdminCrudService.js";

const adminVideoService = new AdminCrudService("video");

let currentPage = 1;
let currentButton = null;
let perPage = 10;
let searchQuery = "";
let sortOrder = "desc";
let searchDebounceTimer = null;

function escapeHtml(value = "") {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function setButtonLoading(button, isLoading) {
    if (!button) return;

    if (isLoading) {
        button.dataset.originalText = button.innerHTML; // Save original
        button.innerHTML = button.dataset.loadingText || "Loading...";
        button.disabled = true;
    } else {
        button.innerHTML = button.dataset.originalText || "Save";
        button.disabled = false;
    }
}

async function loadVideo(page = 1) {
    const tbody = document.getElementById("videoTableBody");
    const modalContainer = document.getElementById("videoModals");
    const pageInfo = document.getElementById("pageInfo");

    // ✅ Show loading row
    tbody.innerHTML = `<tr><td colspan="6" class="text-center">Loading...</td></tr>`;
    modalContainer.innerHTML = "";

    try {
        const data = await adminVideoService.fetchList({
            page,
            perPage,
            order: sortOrder,
            search: searchQuery,
        });

        tbody.innerHTML = ""; // clear loading
        modalContainer.innerHTML = "";

        if (!data.video || data.video.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center">No video found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
            return;
        }

        data.video.forEach((video, index) => {
            const modalIdEdit = `editModal${page}_${index}`;

            // ✅ Add table row
            tbody.innerHTML += `
        <tr>
            <td>${(page - 1) * perPage + (index + 1)}</td>
            <td>
                <div style="max-width: 200px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;"
                    title="${video.title.en}">
                    ${video.title.en}
                </div>
            </td>
            <td>
                <div style="max-width: 200px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;"
                    title="${video.description.en}">
                    ${video.description.en}
                </div>
            </td>
            <td>
                <div style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    <button class="btn btn-sm btn-outline-secondary"
                        onclick="playVideoPreview('${video.video_url || video.file
                }')">
                        ▶ Preview
                    </button>
                </div>
            </td>
            <td>
                <div style="max-width: 200px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;"
                    title="${video.tags?.join(", ") || ""}">
                    ${video.tags?.join(", ") || ""}
                </div>
            </td>
            <td>
                <button class="btn btn-sm btn-primary me-1" data-bs-toggle="modal" data-bs-target="#${modalIdEdit}">
                <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn btn-sm btn-danger video-delete-btn" data-record-id="${video._id}" data-title="${escapeHtml(video.title?.en || "")}">
                <i class="bi bi-trash"></i> Delete
                </button>
            </td>
            </tr>
            `;

            // ✅ Add Edit modal
            modalContainer.innerHTML += `
            <div class="modal fade" id="${modalIdEdit}" tabindex="-1" aria-labelledby="${modalIdEdit}Label" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="${modalIdEdit}Label">Edit Video</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form id="editForm${page}_${index}">
                        <!-- Titles -->
                        <div class="card mb-3">
                            <div class="card-header">
                            <h3 class="card-title">Titles (Multi-language)</h3>
                            </div>
                            <div class="card-body">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Title (EN) <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="editTitleEn${page}_${index}" value="${video.title?.en || ""
                }" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Title (Ceb) <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="editTitleCeb${page}_${index}" value="${video.title?.ceb || ""
                }" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Title (Fr) <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="editTitleFr${page}_${index}" value="${video.title?.fr || ""
                }" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Title (Fil) <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="editTitleFil${page}_${index}" value="${video.title?.fil_PH || ""
                }" required>
                                </div>
                            </div>
                            </div>
                        </div>

                        <!-- Descriptions -->
                        <div class="card mb-3">
                            <div class="card-header">
                            <h3 class="card-title">Descriptions (Multi-language)</h3>
                            </div>
                            <div class="card-body">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Description (EN) <span class="text-danger">*</span></label>
                                <textarea class="form-control" id="editDescriptionEn${page}_${index}" rows="2" required>${video.description?.en || ""
                }</textarea>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Description (Ceb) <span class="text-danger">*</span></label>
                                <textarea class="form-control" id="editDescriptionCeb${page}_${index}" rows="2" required>${video.description?.ceb || ""
                }</textarea>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Description (Fr) <span class="text-danger">*</span></label>
                                <textarea class="form-control" id="editDescriptionFr${page}_${index}" rows="2" required>${video.description?.fr || ""
                }</textarea>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Description (Fil) <span class="text-danger">*</span></label>
                                <textarea class="form-control" id="editDescriptionFil${page}_${index}" rows="2" required>${video.description?.fil_PH || ""
                }</textarea>
                                </div>
                            </div>
                            </div>
                        </div>

                        <!-- Video file -->
                        <div class="mb-3">
                            <label class="form-label">Video File (leave blank to keep current)</label>
                            <input type="file" class="form-control" id="editVideoFile${page}_${index}" accept="video/*">
                        </div>

                        <!-- Tags -->
                        <div class="mb-3">
                            <label class="form-label">Video Tags</label>
                            <input type="text" class="form-control" id="editTags${page}_${index}" value="${(
                    video.tags || []
                ).join(", ")}" placeholder="Comma-separated tags">
                        </div>
                        </form>

                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button
                    type="button"
                    class="btn btn-primary"
                    id="editVideoBtn_${video._id}"
                    data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Saving...'
                    onclick="updateVideo('${video._id
                }', 'editForm${page}_${index}')">Save changes</button>
                </div>
                </div>
            </div>
            </div>
            `;

            setTimeout(() => {
                initDropZone(
                    `editDropZone${page}_${index}`,
                    `editImageFile${page}_${index}`
                );
            }, 0);
        });

        // ✅ Update page info
        pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
        document.getElementById("prevPage").disabled = page <= 1;
        document.getElementById("nextPage").disabled = page == data.total_pages;

        // Attach delete handlers via delegation
        tbody.querySelectorAll(".video-delete-btn").forEach((btn) => {
            btn.addEventListener("click", function () {
                const recordId = this.dataset.recordId;
                const title = this.dataset.title;
                window.confirmDelete(
                    `Are you sure you want to delete <strong>${title}</strong>?`,
                    async () => {
                        const result = await adminVideoService.remove(recordId);
                        if (result.ok) {
                            bootstrap.Modal.getInstance(document.getElementById("deleteConfirmModal")).hide();
                            window.notify(result.data?.message || "Video deleted.", "success");
                            loadVideo(currentPage);
                        } else {
                            window.notify("Failed to delete video.", "error");
                        }
                    }
                );
            });
        });
    } catch (error) {
        console.error("Error fetching video list:", error);
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error loading data</td></tr>`;
    }
}

function validateTags(tags) {
    // Require at least one tag
    if (!tags.length) {
        return "At least one tag is required.";
    }

    // Only allow alphanumeric, dashes, underscores, and spaces
    const invalid = tags.filter((tag) => !/^[a-zA-Z0-9 _-]+$/.test(tag));
    if (invalid.length > 0) {
        return `Invalid tag(s): ${invalid.join(
            ", "
        )}. Allowed: letters, numbers, spaces, dashes, underscores.`;
    }

    return null; // ✅ valid
}

async function addVideo() {
    const btn = document.getElementById("addVideoBtn");
    setButtonLoading(btn, true);

    const titles = {
        en: document.getElementById("addTitle").value.trim(),
        ceb: document.getElementById("addTitleCeb").value.trim(),
        fr: document.getElementById("addTitleFr").value.trim(),
        fil_PH: document.getElementById("addTitleFil").value.trim(),
    };

    const descriptions = {
        en: document.getElementById("addDescription").value.trim(),
        ceb: document.getElementById("addDescriptionCeb").value.trim(),
        fr: document.getElementById("addDescriptionFr").value.trim(),
        fil_PH: document.getElementById("addDescriptionFil").value.trim(),
    };
    const videoFile = document.getElementById("addVideoFile").files[0];
    const tags = document
        .getElementById("addTags")
        .value.split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);

    // ✅ Require ALL translations + video file
    if (
        !titles.en ||
        !titles.ceb ||
        !titles.fr ||
        !titles.fil_PH ||
        !descriptions.en ||
        !descriptions.ceb ||
        !descriptions.fr ||
        !descriptions.fil_PH ||
        !videoFile
    ) {
        window.notify("All titles, descriptions, and a video file are required.", "warning");
        setButtonLoading(btn, false);
        return;
    }

    // ✅ File type validation
    if (!videoFile.type.startsWith("video/")) {
        window.notify("Please upload a valid video file.", "warning");
        setButtonLoading(btn, false);
        return;
    }

    // ✅ Validate tags
    const tagError = validateTags(tags);
    if (tagError) {
        window.notify(tagError, "warning");
        setButtonLoading(btn, false);
        return;
    }

    const formData = new FormData();
    formData.append("title", JSON.stringify(titles));
    formData.append("description", JSON.stringify(descriptions));
    formData.append("tags", JSON.stringify(tags));
    formData.append("video_file", videoFile);

    try {
        const result = await adminVideoService.add(formData);
        if (result.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById("addVideoModal")
            ).hide();
            loadVideo(currentPage);
            window.notify(result.data?.message || "Video added.", "success");
        } else {
            window.notify("Failed to add video.", "error");
        }
    } catch (err) {
        console.error(err);
        window.notify("Error adding video.", "error");
    } finally {
        setButtonLoading(btn, false);
    }
}

async function updateVideo(videoId, formId) {
    const btn = document.getElementById(`editVideoBtn_${videoId}`);
    setButtonLoading(btn, true);

    const form = document.getElementById(formId);
    const suffix = formId.replace("editForm", ""); // e.g. "_1_0"
    // ✅ Collect multi-language titles
    const titles = {
        en: form.querySelector(`#editTitleEn${suffix}`).value.trim(),
        ceb: form.querySelector(`#editTitleCeb${suffix}`).value.trim(),
        fr: form.querySelector(`#editTitleFr${suffix}`).value.trim(),
        fil_PH: form.querySelector(`#editTitleFil${suffix}`).value.trim(),
    };
    // ✅ Collect multi-language descriptions
    const descriptions = {
        en: form.querySelector(`#editDescriptionEn${suffix}`).value.trim(),
        ceb: form.querySelector(`#editDescriptionCeb${suffix}`).value.trim(),
        fr: form.querySelector(`#editDescriptionFr${suffix}`).value.trim(),
        fil_PH: form.querySelector(`#editDescriptionFil${suffix}`).value.trim(),
    };
    const videoFile = form.querySelector(`#editVideoFile${suffix}`).files[0];
    // ✅ Collect tags
    const tags = form
        .querySelector(`#editTags${suffix}`)
        .value.split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);

    // ✅ Require ALL translations (file optional for update)
    if (
        !titles.en ||
        !titles.ceb ||
        !titles.fr ||
        !titles.fil_PH ||
        !descriptions.en ||
        !descriptions.ceb ||
        !descriptions.fr ||
        !descriptions.fil_PH
    ) {
        window.notify("All titles and descriptions are required.", "warning");
        setButtonLoading(btn, false);
        return;
    }

    if (videoFile && !videoFile.type.startsWith("video/")) {
        window.notify("Please upload a valid video file.", "warning");
        setButtonLoading(btn, false);
        return;
    }

    // ✅ Validate tags
    const tagError = validateTags(tags);
    if (tagError) {
        window.notify(tagError, "warning");
        setButtonLoading(btn, false);
        return;
    }

    const formData = new FormData();
    formData.append("title", JSON.stringify(titles));
    formData.append("description", JSON.stringify(descriptions));
    formData.append("tags", JSON.stringify(tags));
    if (videoFile) formData.append("video_file", videoFile);

    try {
        const result = await adminVideoService.update(videoId, formData);
        if (result.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById(form.closest(".modal").id)
            ).hide();

            loadVideo(currentPage);
            window.notify(result.data?.message || "Video updated.", "success");
        } else {
            window.notify("Failed to update video.", "error");
        }
    } catch (err) {
        console.error(err);
        window.notify("Error updating video.", "error");
    } finally {
        // 🔹 Restore button
        setButtonLoading(btn, false);
    }
}

async function deleteVideo(videoId) {
    const result = await adminVideoService.remove(videoId);
    if (result.ok) {
        loadVideo(currentPage);
        window.notify(result.data?.message || "Video deleted.", "success");
    } else {
        window.notify("Failed to delete video.", "error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadVideo(currentPage);

    const addVideoModal = document.getElementById("addVideoModal");
    addVideoModal.addEventListener("show.bs.modal", () => {
        document.getElementById("addVideoForm").reset();
    });

    document.getElementById("prevPage").addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            loadVideo(currentPage);
        }
    });

    document.getElementById("nextPage").addEventListener("click", () => {
        currentPage++;
        loadVideo(currentPage);
    });

    document.getElementById("perPageSelect").addEventListener("change", (e) => {
        perPage = parseInt(e.target.value);
        currentPage = 1; // reset to first page when perPage changes
        loadVideo(currentPage);
    });

    const searchInput = document.getElementById("searchInput");
    const orderSelect = document.getElementById("orderSelect");

    searchInput?.addEventListener("input", (event) => {
        const nextValue = String(event.target.value || "").trim();
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            searchQuery = nextValue;
            currentPage = 1;
            loadVideo(currentPage);
        }, 300);
    });

    orderSelect?.addEventListener("change", (event) => {
        sortOrder = String(event.target.value || "desc");
        currentPage = 1;
        loadVideo(currentPage);
    });
});

window.addVideo = addVideo;
window.updateVideo = updateVideo;
window.deleteVideo = deleteVideo;

