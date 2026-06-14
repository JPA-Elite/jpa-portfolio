import { AdminCrudService } from "../../services/AdminCrudService.js";

const adminGalleryService = new AdminCrudService("gallery");

let currentPage = 1;
let currentButton = null;
let perPage = 10;
let searchQuery = "";
let sortOrder = "desc";
let searchDebounceTimer = null;

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

function escapeHtml(value = "") {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function initDropZone(dropZoneId, inputId) {
    const dropZone = document.getElementById(dropZoneId);
    const inputEl = document.getElementById(inputId);

    if (!dropZone || !inputEl) return;

    dropZone.addEventListener("click", () => inputEl.click());

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation(); // ✅ stop modal/backdrop from stealing event
            dropZone.classList.add("dragover");
        });
    });

    dropZone.addEventListener("dragleave", (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("dragover");

        if (e.dataTransfer.files.length > 0) {
            inputEl.files = e.dataTransfer.files;
            dropZone.querySelector("p").textContent = e.dataTransfer.files[0].name;
        }
    });

    inputEl.addEventListener("change", () => {
        if (inputEl.files.length > 0) {
            dropZone.querySelector("p").textContent = inputEl.files[0].name;
        }
    });
}

async function loadGallery(page = 1) {
    const tbody = document.getElementById("galleryTableBody");
    const modalContainer = document.getElementById("galleryModals");
    const pageInfo = document.getElementById("pageInfo");

    // ✅ Show loading row
    tbody.innerHTML = `<tr><td colspan="6" class="text-center">Loading...</td></tr>`;
    modalContainer.innerHTML = "";

    try {
        const data = await adminGalleryService.fetchList({
            page,
            perPage,
            order: sortOrder,
            search: searchQuery,
        });

        tbody.innerHTML = ""; // clear loading
        modalContainer.innerHTML = "";

        if (!data.gallery || data.gallery.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center">No gallery found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
            return;
        }

        data.gallery.forEach((gallery, index) => {
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
                    title="${gallery.title.en}">
                    ${gallery.title.en}
                </div>
            </td>
            <td>
                <div style="max-width: 200px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;"
                    title="${gallery.description.en}">
                    ${gallery.description.en}
                </div>
            </td>
            <td>
                <img src="${gallery.image_url
                }" onclick="playGalleryPreview('${gallery.image_url}')" alt="${gallery.title.en
                }" style="cursor: pointer; width: 60px; height: auto; border-radius:4px;">
            </td>
            <td>
                <div style="max-width: 200px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;"
                    title="${gallery.tags?.join(", ") || ""}">
                    ${gallery.tags?.join(", ") || ""}
                </div>
            </td>
            <td>
                <button class="btn btn-sm btn-primary me-1" data-bs-toggle="modal" data-bs-target="#${modalIdEdit}">
                <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn btn-sm btn-danger gallery-delete-btn" data-record-id="${gallery._id}" data-title="${escapeHtml(gallery.title?.en || "")}">
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
                    <h5 class="modal-title me-auto" id="${modalIdEdit}Label">Edit Gallery</h5>
                    <div class="d-flex align-items-center gap-1">
                        <button type="button" class="btn p-1 preview-header-btn edit-maximize-btn" data-target-modal="${modalIdEdit}" aria-label="Maximize" title="Maximize">
                            <i class="bi bi-arrows-fullscreen"></i>
                        </button>
                        <button type="button" class="btn p-1 preview-header-btn" data-bs-dismiss="modal" aria-label="Close">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
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
                                <input type="text" class="form-control" id="editTitleEn${page}_${index}" value="${gallery.title?.en || ""
                }" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Title (Ceb) <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="editTitleCeb${page}_${index}" value="${gallery.title?.ceb || ""
                }" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Title (Fr) <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="editTitleFr${page}_${index}" value="${gallery.title?.fr || ""
                }" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Title (Fil) <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="editTitleFil${page}_${index}" value="${gallery.title?.fil_PH || ""
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
                                <textarea class="form-control" id="editDescriptionEn${page}_${index}" rows="2" required>${gallery.description?.en || ""
                }</textarea>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Description (Ceb) <span class="text-danger">*</span></label>
                                <textarea class="form-control" id="editDescriptionCeb${page}_${index}" rows="2" required>${gallery.description?.ceb || ""
                }</textarea>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Description (Fr) <span class="text-danger">*</span></label>
                                <textarea class="form-control" id="editDescriptionFr${page}_${index}" rows="2" required>${gallery.description?.fr || ""
                }</textarea>
                                </div>
                                <div class="col-md-6 mb-3">
                                <label class="form-label">Description (Fil) <span class="text-danger">*</span></label>
                                <textarea class="form-control" id="editDescriptionFil${page}_${index}" rows="2" required>${gallery.description?.fil_PH || ""
                }</textarea>
                                </div>
                            </div>
                            </div>
                        </div>

                        <!-- Desktop (Drag & Drop) -->
                        <div class="mb-3 d-none d-md-block">
                            <label class="form-label">Image File (leave blank to keep current)</label>
                            <div id="editDropZone${page}_${index}" class="dropzone">
                                <p>Drag & Drop image here, or click to select</p>
                                <input type="file" id="editImageFile${page}_${index}" accept="image/*" hidden>
                            </div>
                        </div>

                        <!-- Mobile (Normal Input) -->
                        <div class="mb-3 d-md-none">
                            <label class="form-label">Image File (leave blank to keep current)</label>
                            <input type="file" class="form-control" id="editImageFileMobile${page}_${index}" accept="image/*">
                        </div>

                        <!-- Tags -->
                        <div class="mb-3">
                            <label class="form-label">Gallery Tags</label>
                            <input type="text" class="form-control" id="editTags${page}_${index}" value="${(
                    gallery.tags || []
                ).join(", ")}" placeholder="Comma-separated tags">
                        </div>
                        </form>

                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button
                    type="button"
                    class="btn btn-primary"
                    id="editGalleryBtn_${gallery._id}"
                    data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Saving...'
                    onclick="updateGallery('${gallery._id
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
        tbody.querySelectorAll(".gallery-delete-btn").forEach((btn) => {
            btn.addEventListener("click", function () {
                const recordId = this.dataset.recordId;
                const title = this.dataset.title;
                window.confirmDelete(
                    `Are you sure you want to delete <strong>${title}</strong>?`,
                    async () => {
                        const result = await adminGalleryService.remove(recordId);
                        if (result.ok) {
                            bootstrap.Modal.getInstance(document.getElementById("deleteConfirmModal")).hide();
                            window.notify(result.data?.message || "Gallery deleted.", "success");
                            loadGallery(currentPage);
                        } else {
                            window.notify("Failed to delete gallery.", "error");
                        }
                    }
                );
            });
        });
    } catch (error) {
        console.error("Error fetching gallery list:", error);
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

function playGalleryPreview(url) {
    if (typeof window.openAdminImagePreview !== "function") {
        console.error("openAdminImagePreview is not available.");
        return;
    }
    window.openAdminImagePreview(url, "Gallery Image");
}

function toggleGalleryModalMaximize(btn) {
    const modalId = btn.dataset.targetModal || btn.closest(".modal")?.id;
    if (!modalId) return;
    const dialog = document.querySelector("#" + modalId + " .modal-dialog");
    const modalBody = dialog?.querySelector(".modal-body");
    if (!dialog) return;
    dialog.classList.toggle("modal-fullscreen");
    const isFull = dialog.classList.contains("modal-fullscreen");

    // Adjust modal-body max-height for better fullscreen experience
    if (modalBody) {
        modalBody.style.maxHeight = isFull ? "calc(100vh - 120px)" : "";
    }

    btn.innerHTML = isFull
        ? '<i class="bi bi-fullscreen-exit"></i>'
        : '<i class="bi bi-arrows-fullscreen"></i>';
    btn.setAttribute("title", isFull ? "Restore" : "Maximize");
    btn.setAttribute("aria-label", isFull ? "Restore" : "Maximize");
}

async function addGallery() {
    const btn = document.getElementById("addGalleryBtn");
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
    const imageFileDesktop = document.getElementById("addImageFile").files[0];
    const imageFileMobile =
        document.getElementById("addImageFileMobile").files[0];
    const imageFile = imageFileDesktop || imageFileMobile;
    const tags = document
        .getElementById("addTags")
        .value.split(",")
        .map((tag) => tag.trim())
        .filter(Boolean);

    // ✅ Require ALL translations + gallery file
    if (
        !titles.en ||
        !titles.ceb ||
        !titles.fr ||
        !titles.fil_PH ||
        !descriptions.en ||
        !descriptions.ceb ||
        !descriptions.fr ||
        !descriptions.fil_PH ||
        !imageFile
    ) {
        window.notify("All titles, descriptions, and a gallery file are required.", "warning");
        setButtonLoading(btn, false);
        return;
    }

    if (!imageFile.type.startsWith("image/")) {
        window.notify("Please upload a valid image file.", "warning");
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
    formData.append("image_file", imageFile);

    try {
        const result = await adminGalleryService.add(formData);
        if (result.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById("addGalleryModal")
            ).hide();
            loadGallery(currentPage);
            window.notify(result.data?.message || "Gallery added.", "success");
        } else {
            window.notify("Failed to add gallery.", "error");
        }
    } catch (err) {
        console.error(err);
        window.notify("Error adding gallery.", "error");
    } finally {
        setButtonLoading(btn, false);
    }
}

async function updateGallery(galleryId, formId) {
    const btn = document.getElementById(`editGalleryBtn_${galleryId}`);
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
    const imageFileDesktop = form.querySelector(
        `#${formId} input[id^='editImageFile']`
    ).files[0];
    const imageFileMobile = form.querySelector(
        `#${formId} input[id^='editImageFileMobile']`
    ).files[0];
    const imageFile = imageFileDesktop || imageFileMobile;

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

    if (imageFile && !imageFile.type.startsWith("image/")) {
        window.notify("Please upload a valid image file.", "warning");
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
    if (imageFile) formData.append("image_file", imageFile);

    try {
        const result = await adminGalleryService.update(galleryId, formData);
        if (result.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById(form.closest(".modal").id)
            ).hide();

            loadGallery(currentPage);
            window.notify(result.data?.message || "Gallery updated.", "success");
        } else {
            window.notify("Failed to update gallery.", "error");
        }
    } catch (err) {
        console.error(err);
        window.notify("Error updating gallery.", "error");
    } finally {
        // 🔹 Restore button
        setButtonLoading(btn, false);
    }
}

async function deleteGallery(galleryId) {
    const result = await adminGalleryService.remove(galleryId);
    if (result.ok) {
        loadGallery(currentPage);
        window.notify(result.data?.message || "Gallery deleted.", "success");
    } else {
        window.notify("Failed to delete gallery.", "error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Add Gallery maximize handler
    const addMaxBtn = document.getElementById("addGalleryMaximizeBtn");
    if (addMaxBtn) {
        addMaxBtn.dataset.targetModal = "addGalleryModal";
        addMaxBtn.addEventListener("click", function () {
            toggleGalleryModalMaximize(this);
        });
    }

    // Delegated handler for edit maximize buttons (dynamically created)
    document.addEventListener("click", function (e) {
        const btn = e.target.closest(".edit-maximize-btn");
        if (btn) {
            const modalId = btn.dataset.targetModal;
            if (modalId) {
                toggleGalleryModalMaximize(btn);
            }
        }
    });

    loadGallery(currentPage);
    initDropZone("addDropZone", "addImageFile");

    const addGalleryModal = document.getElementById("addGalleryModal");
    addGalleryModal.addEventListener("show.bs.modal", () => {
        document.getElementById("addGalleryForm").reset();

        // reset dropzone text
        const addDropZone = document.getElementById("addDropZone");
        if (addDropZone) {
            const p = addDropZone.querySelector("p");
            if (p) p.textContent = "Drag & Drop image here, or click to select";
        }
    });

    document.getElementById("prevPage").addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            loadGallery(currentPage);
        }
    });

    document.getElementById("nextPage").addEventListener("click", () => {
        currentPage++;
        loadGallery(currentPage);
    });

    document.getElementById("perPageSelect").addEventListener("change", (e) => {
        perPage = parseInt(e.target.value);
        currentPage = 1; // reset to first page when perPage changes
        loadGallery(currentPage);
    });

    const searchInput = document.getElementById("searchInput");
    const orderSelect = document.getElementById("orderSelect");

    searchInput?.addEventListener("input", (event) => {
        const nextValue = String(event.target.value || "").trim();
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            searchQuery = nextValue;
            currentPage = 1;
            loadGallery(currentPage);
        }, 300);
    });

    orderSelect?.addEventListener("change", (event) => {
        sortOrder = String(event.target.value || "desc");
        currentPage = 1;
        loadGallery(currentPage);
    });
});

window.addGallery = addGallery;
window.updateGallery = updateGallery;
window.deleteGallery = deleteGallery;
window.playGalleryPreview = playGalleryPreview;

