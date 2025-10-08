let currentPage = 1;
let currentButton = null;
let perPage = 10;

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
        const response = await fetch(
            `/admin/api/gallery-list?page=${page}&per_page=${perPage}&order=desc`
        );
        const data = await response.json();

        tbody.innerHTML = ""; // clear loading
        modalContainer.innerHTML = "";

        if (!data.gallery || data.gallery.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center">No gallery found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
            return;
        }

        data.gallery.forEach((gallery, index) => {
            const modalIdEdit = `editModal${page}_${index}`;
            const modalIdDelete = `deleteModal${page}_${index}`;

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
                }" onclick="window.location.href='${gallery.image_url}'" alt="${gallery.title.en
                }" style="width: 60px; height: auto; border-radius:4px;">
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
                <button class="btn btn-sm btn-danger" data-bs-toggle="modal" data-bs-target="#${modalIdDelete}">
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
                    <h5 class="modal-title" id="${modalIdEdit}Label">Edit Gallery</h5>
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

            // ✅ Add Delete modal
            modalContainer.innerHTML += `
            <div class="modal fade" id="${modalIdDelete}" tabindex="-1" aria-labelledby="${modalIdDelete}Label" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="${modalIdDelete}Label">Delete Gallery</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    Are you sure you want to delete <strong>${gallery.title.en}</strong>?
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-danger" onclick="deleteGallery('${gallery._id}', '${modalIdDelete}')">Delete</button>
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
        alert("All titles, descriptions, and a gallery file are required.");
        setButtonLoading(btn, false);
        return;
    }

    if (!imageFile.type.startsWith("image/")) {
        alert("Please upload a valid image file.");
        setButtonLoading(btn, false);
        return;
    }

    // ✅ Validate tags
    const tagError = validateTags(tags);
    if (tagError) {
        alert(tagError);
        setButtonLoading(btn, false);
        return;
    }

    const formData = new FormData();
    formData.append("title", JSON.stringify(titles));
    formData.append("description", JSON.stringify(descriptions));
    formData.append("tags", JSON.stringify(tags));
    formData.append("image_file", imageFile);

    try {
        const res = await fetch("/admin/api/add-gallery", {
            method: "POST",
            body: formData,
        });

        if (res.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById("addGalleryModal")
            ).hide();
            const data = await res.json();
            loadGallery(currentPage);
            alert(data.message);
        } else {
            alert("Failed to add gallery.");
        }
    } catch (err) {
        console.error(err);
        alert("Error adding gallery.");
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
        alert("All titles and descriptions are required.");
        setButtonLoading(btn, false);
        return;
    }

    if (imageFile && !imageFile.type.startsWith("image/")) {
        alert("Please upload a valid image file.");
        setButtonLoading(btn, false);
        return;
    }

    // ✅ Validate tags
    const tagError = validateTags(tags);
    if (tagError) {
        alert(tagError);
        setButtonLoading(btn, false);
        return;
    }

    const formData = new FormData();
    formData.append("title", JSON.stringify(titles));
    formData.append("description", JSON.stringify(descriptions));
    formData.append("tags", JSON.stringify(tags));
    if (imageFile) formData.append("image_file", imageFile);

    try {
        const res = await fetch(`/admin/api/update-gallery/${galleryId}`, {
            method: "PUT",
            body: formData,
        });

        if (res.ok) {
            bootstrap.Modal.getInstance(
                document.getElementById(form.closest(".modal").id)
            ).hide();

            const data = await res.json();
            loadGallery(currentPage);
            alert(data.message);
        } else {
            alert("Failed to update gallery.");
        }
    } catch (err) {
        console.error(err);
        alert("Error updating gallery.");
    } finally {
        // 🔹 Restore button
        setButtonLoading(btn, false);
    }
}

async function deleteGallery(galleryId, modalId) {
    const res = await fetch(`/admin/api/delete-gallery/${galleryId}`, {
        method: "DELETE",
    });

    if (res.ok) {
        bootstrap.Modal.getInstance(document.getElementById(modalId)).hide();
        const data = await res.json();
        loadGallery(currentPage);
        alert(data.message);
    } else {
        alert("Failed to delete gallery.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
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
});
