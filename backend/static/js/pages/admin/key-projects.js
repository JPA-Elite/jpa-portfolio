import { AdminCrudService } from "../../services/AdminCrudService.js";

const adminKeyProjectService = new AdminCrudService("key-project");

let currentPage = 1;
let perPage = 10;
let searchQuery = "";
let sortOrder = "asc";
let statusFilter = "";
let activeFilter = "";
let searchDebounceTimer = null;

function setButtonLoading(button, isLoading) {
    if (!button) return;
    if (isLoading) {
        button.dataset.originalText = button.innerHTML;
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

function statusLabel(status) {
    if (status === "shipped") return "Shipped";
    if (status === "building") return "Building";
    return "Planned";
}

function buildI18nPayload(prefix, suffix = "") {
    const id = (base) => document.getElementById(`${prefix}${base}${suffix}`);
    return {
        en: id("TitleEn") ? id("TitleEn").value.trim() : id("DescEn").value.trim(),
        ceb: id("TitleCeb") ? id("TitleCeb").value.trim() : id("DescCeb").value.trim(),
        fr: id("TitleFr") ? id("TitleFr").value.trim() : id("DescFr").value.trim(),
        fil_PH: id("TitleFil") ? id("TitleFil").value.trim() : id("DescFil").value.trim(),
    };
}

function getTitles(prefix, suffix = "") {
    const get = (id) => document.getElementById(`${prefix}${id}${suffix}`);
    return {
        en: get("TitleEn").value.trim(),
        ceb: get("TitleCeb").value.trim(),
        fr: get("TitleFr").value.trim(),
        fil_PH: get("TitleFil").value.trim(),
    };
}

function getDescriptions(prefix, suffix = "") {
    const get = (id) => document.getElementById(`${prefix}${id}${suffix}`);
    return {
        en: get("DescEn").value.trim(),
        ceb: get("DescCeb").value.trim(),
        fr: get("DescFr").value.trim(),
        fil_PH: get("DescFil").value.trim(),
    };
}

function buildStatusBadge(status) {
    const color = status === "shipped" ? "success" : status === "building" ? "warning" : "secondary";
    return `<span class="badge text-bg-${color}">${statusLabel(status)}</span>`;
}

function buildSlideRowMarkup(slide = {}) {
    const title = slide.title?.en || slide.title || "";
    const description = slide.description?.en || slide.description || "";
    const existingImageUrl = slide.image_url || "";
    const slideId = slide.id || "";

    return `
    <div class="project-slide-row border rounded p-2" data-slide-row data-slide-id="${escapeHtml(slideId)}" data-existing-image-url="${escapeHtml(existingImageUrl)}">
      <div class="row g-2 align-items-start">
        <div class="col-md-3">
          <label class="form-label mb-1">Slide Image</label>
          ${existingImageUrl ? `<div class="mb-1"><img src="${escapeHtml(existingImageUrl)}" alt="Slide preview" style="width:100%;max-height:90px;object-fit:cover;border-radius:6px;border:1px solid #ddd;"></div>` : ""}
          <input type="file" class="form-control form-control-sm" accept="image/*" data-slide-file>
          <div class="form-text">Upload to add/replace this slide image.</div>
        </div>
        <div class="col-md-3">
          <label class="form-label mb-1">Slide Title</label>
          <input type="text" class="form-control form-control-sm" value="${escapeHtml(title)}" data-slide-title placeholder="Overview">
        </div>
        <div class="col-md-5">
          <label class="form-label mb-1">Slide Description</label>
          <textarea class="form-control form-control-sm" rows="3" data-slide-description placeholder="What this screenshot shows...">${escapeHtml(description)}</textarea>
        </div>
        <div class="col-md-1 d-grid">
          <label class="form-label mb-1">&nbsp;</label>
          <button type="button" class="btn btn-outline-danger btn-sm" data-remove-slide-row title="Remove slide">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    </div>`;
}

function serializeSlideRows(container, formData) {
    if (!container) return [];

    const rows = Array.from(container.querySelectorAll("[data-slide-row]"));
    const slidesMeta = [];

    rows.forEach((row, index) => {
        const fileInput = row.querySelector("[data-slide-file]");
        const titleInput = row.querySelector("[data-slide-title]");
        const descInput = row.querySelector("[data-slide-description]");

        const title = (titleInput?.value || "").trim();
        const description = (descInput?.value || "").trim();
        const existingImageUrl = row.dataset.existingImageUrl || "";
        const slideId = row.dataset.slideId || "";

        let imageField = "";
        const file = fileInput?.files?.[0];
        if (file) {
            imageField = `slide_file_${Date.now()}_${index}_${Math.random().toString(36).slice(2, 8)}`;
            formData.append(imageField, file);
        }

        if (!imageField && !existingImageUrl) {
            // Ignore empty rows that were added but not filled.
            if (!title && !description) return;
            throw new Error(`Slide ${index + 1}: image is required.`);
        }

        slidesMeta.push({
            id: slideId || null,
            image_field: imageField,
            existing_image_url: existingImageUrl || null,
            title,
            description,
            sort_order: index,
        });
    });

    return slidesMeta;
}

function appendSlideRow(containerSelector, slide = {}) {
    const container = typeof containerSelector === "string"
        ? document.querySelector(containerSelector)
        : containerSelector;
    if (!container) return;
    container.insertAdjacentHTML("beforeend", buildSlideRowMarkup(slide));
}

async function loadKeyProjects(page = 1) {
    const tbody = document.getElementById("keyProjectsTableBody");
    const modalContainer = document.getElementById("keyProjectModals");
    const pageInfo = document.getElementById("pageInfo");

    tbody.innerHTML = `<tr><td colspan="9" class="text-center">Loading...</td></tr>`;
    modalContainer.innerHTML = "";

    try {
        const data = await adminKeyProjectService.fetchList({
            page,
            perPage,
            order: sortOrder,
            search: searchQuery,
            status: statusFilter,
            is_active: activeFilter,
        });
        const rows = data.projects || [];

        tbody.innerHTML = "";

        if (!rows.length) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center">No key projects found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages || 1}`;
            document.getElementById("prevPage").disabled = true;
            document.getElementById("nextPage").disabled = true;
            return;
        }

        rows.forEach((project, index) => {
            const rowNo = (page - 1) * perPage + index + 1;
            const editModalId = `editProjectModal_${page}_${index}`;
            const deleteModalId = `deleteProjectModal_${page}_${index}`;
            const img = project.image_url || "";
            const safeTitle = escapeHtml(project.title?.en || "Untitled");
            const safeStack = escapeHtml(project.stack || "");
            const slideCount = Array.isArray(project.slides) ? project.slides.length + (project.image_url ? 1 : 0) : (project.image_url ? 1 : 0);

            tbody.insertAdjacentHTML("beforeend", `
                <tr>
                    <td>${rowNo}</td>
                    <td style="width:90px;">
                        ${img ? `<img
                            src="${escapeHtml(img)}"
                            alt="${safeTitle}"
                            data-preview-src="${escapeHtml(img)}"
                            data-preview-title="${safeTitle}"
                            onclick="playKeyProjectPreview(this.dataset.previewSrc, this.dataset.previewTitle)"
                            style="cursor:pointer;width:64px;height:48px;object-fit:cover;border-radius:6px;border:1px solid #ddd;">` : `<span class="text-muted">No image</span>`}
                    </td>
                    <td>
                        <div style="max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${safeTitle}">
                            ${safeTitle}
                        </div>
                    </td>
                    <td>
                        <div style="max-width: 170px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${safeStack}">
                            ${safeStack || "-"}
                        </div>
                    </td>
                    <td>${buildStatusBadge(project.status)}</td>
                    <td><span class="badge text-bg-info">${slideCount}</span></td>
                    <td>${Number(project.sort_order || 0)}</td>
                    <td>${project.is_active === false ? '<span class="badge text-bg-secondary">No</span>' : '<span class="badge text-bg-success">Yes</span>'}</td>
                    <td>
                        <div class="kp-admin-actions">
                            <button class="btn btn-sm btn-primary me-1" data-bs-toggle="modal" data-bs-target="#${editModalId}">
                                <i class="bi bi-pencil"></i> Edit
                            </button>
                            <button class="btn btn-sm btn-danger" data-bs-toggle="modal" data-bs-target="#${deleteModalId}">
                                <i class="bi bi-trash"></i> Delete
                            </button>
                        </div>
                    </td>
                </tr>
            `);

            modalContainer.insertAdjacentHTML("beforeend", buildEditModal(project, editModalId, page, index));
            modalContainer.insertAdjacentHTML("beforeend", buildDeleteModal(project, deleteModalId));
        });

        pageInfo.textContent = `Page ${page} | ${data.total_pages || 1}`;
        document.getElementById("prevPage").disabled = page <= 1;
        document.getElementById("nextPage").disabled = page >= (data.total_pages || 1);
    } catch (error) {
        console.error(error);
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">Error loading key projects</td></tr>`;
    }
}

function playKeyProjectPreview(url, title = "Key Project Image") {
    if (typeof window.openAdminImagePreview !== "function") {
        console.error("openAdminImagePreview is not available.");
        return;
    }
    window.openAdminImagePreview(url, title || "Key Project Image");
}

function buildEditModal(project, modalId, page, index) {
    const suffix = `_${page}_${index}`;
    const p = {
        title: project.title || {},
        description: project.description || {},
    };
    const slides = Array.isArray(project.slides) ? project.slides : [];
    const slidesMarkup = slides.map((slide) => buildSlideRowMarkup(slide)).join("");

    return `
    <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Key Project</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <form id="editProjectForm${suffix}">
              <div class="row g-3">
                <div class="col-12">
                  <label class="form-label">Replace Image (optional)</label>
                  <input type="file" id="editImageFile${suffix}" class="form-control" accept="image/*">
                </div>
                <div class="col-md-6">
                  <label class="form-label">Stack / Tech</label>
                  <input type="text" id="editStack${suffix}" class="form-control" value="${escapeHtml(project.stack || "")}">
                </div>
                <div class="col-md-3">
                  <label class="form-label">Status</label>
                  <select id="editStatus${suffix}" class="form-select">
                    <option value="shipped" ${project.status === "shipped" ? "selected" : ""}>Shipped</option>
                    <option value="building" ${project.status === "building" ? "selected" : ""}>Building</option>
                    <option value="planned" ${project.status === "planned" ? "selected" : ""}>Planned</option>
                  </select>
                </div>
                <div class="col-md-3">
                  <label class="form-label">Sort Order</label>
                  <input type="number" id="editSortOrder${suffix}" class="form-control" value="${Number(project.sort_order || 0)}">
                </div>

                <div class="col-md-6"><label class="form-label">Title (EN)</label><input type="text" id="editTitleEn${suffix}" class="form-control" value="${escapeHtml(p.title.en || "")}"></div>
                <div class="col-md-6"><label class="form-label">Title (Ceb)</label><input type="text" id="editTitleCeb${suffix}" class="form-control" value="${escapeHtml(p.title.ceb || "")}"></div>
                <div class="col-md-6"><label class="form-label">Title (Fr)</label><input type="text" id="editTitleFr${suffix}" class="form-control" value="${escapeHtml(p.title.fr || "")}"></div>
                <div class="col-md-6"><label class="form-label">Title (Fil)</label><input type="text" id="editTitleFil${suffix}" class="form-control" value="${escapeHtml(p.title.fil_PH || "")}"></div>

                <div class="col-md-6"><label class="form-label">Description (EN)</label><textarea id="editDescEn${suffix}" class="form-control" rows="2">${escapeHtml(p.description.en || "")}</textarea></div>
                <div class="col-md-6"><label class="form-label">Description (Ceb)</label><textarea id="editDescCeb${suffix}" class="form-control" rows="2">${escapeHtml(p.description.ceb || "")}</textarea></div>
                <div class="col-md-6"><label class="form-label">Description (Fr)</label><textarea id="editDescFr${suffix}" class="form-control" rows="2">${escapeHtml(p.description.fr || "")}</textarea></div>
                <div class="col-md-6"><label class="form-label">Description (Fil)</label><textarea id="editDescFil${suffix}" class="form-control" rows="2">${escapeHtml(p.description.fil_PH || "")}</textarea></div>

                <div class="col-12">
                  <div class="card border">
                    <div class="card-header d-flex justify-content-between align-items-center">
                      <strong>Additional Slides (for modal arrows)</strong>
                      <button type="button" class="btn btn-sm btn-outline-primary" data-add-slide-row data-target="#editProjectSlidesContainer${suffix}">
                        <i class="bi bi-plus"></i> Add Slide
                      </button>
                    </div>
                    <div class="card-body">
                      <p class="text-muted small mb-2">Cover image is included automatically as the first slide. Add/replace extra slides here.</p>
                      <div id="editProjectSlidesContainer${suffix}" class="d-grid gap-2">${slidesMarkup}</div>
                    </div>
                  </div>
                </div>

                <div class="col-md-6"><label class="form-label">Demo URL</label><input type="url" id="editDemoUrl${suffix}" class="form-control" value="${escapeHtml(project.demo_url || "")}"></div>
                <div class="col-md-6"><label class="form-label">Repo URL</label><input type="url" id="editRepoUrl${suffix}" class="form-control" value="${escapeHtml(project.repo_url || "")}"></div>

                <div class="col-12 form-check mt-2 ms-2">
                  <input class="form-check-input" type="checkbox" id="editIsActive${suffix}" ${project.is_active === false ? "" : "checked"}>
                  <label class="form-check-label" for="editIsActive${suffix}">Active (show on profile)</label>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-primary" id="editProjectBtn_${project._id}"
              data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Saving...'
              onclick="updateKeyProject('${project._id}', '${suffix}')">Save changes</button>
          </div>
        </div>
      </div>
    </div>`;
}

function buildDeleteModal(project, modalId) {
    return `
    <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Delete Key Project</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            Are you sure you want to delete <strong>${escapeHtml(project.title?.en || "this project")}</strong>?
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-danger" id="deleteProjectBtn_${project._id}"
              data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Deleting...'
              onclick="deleteKeyProject('${project._id}', '${modalId}')">Delete</button>
          </div>
        </div>
      </div>
    </div>`;
}

async function addKeyProject() {
    const button = document.getElementById("addProjectBtn");
    setButtonLoading(button, true);

    try {
        const imageFile = document.getElementById("addImageFile").files[0];
        if (!imageFile) {
            window.notify("Image is required.", "warning");
            return;
        }

        const titles = getTitles("add");
        const descriptions = getDescriptions("add");

        const formData = new FormData();
        formData.append("title", JSON.stringify(titles));
        formData.append("description", JSON.stringify(descriptions));
        formData.append("image_file", imageFile);
        formData.append("stack", document.getElementById("addStack").value.trim());
        formData.append("status", document.getElementById("addStatus").value);
        formData.append("sort_order", document.getElementById("addSortOrder").value || "0");
        formData.append("demo_url", document.getElementById("addDemoUrl").value.trim());
        formData.append("repo_url", document.getElementById("addRepoUrl").value.trim());
        formData.append("is_active", document.getElementById("addIsActive").checked ? "true" : "false");
        const addSlidesContainer = document.getElementById("addProjectSlidesContainer");
        formData.append("slides_meta", JSON.stringify(serializeSlideRows(addSlidesContainer, formData)));

        const result = await adminKeyProjectService.add(formData);
        if (!result.ok) throw new Error(result.data?.message || "Failed to add project");

        window.notify(result.data?.message || "Added", "success");
        const modalEl = document.getElementById("addProjectModal");
        bootstrap.Modal.getInstance(modalEl)?.hide();
        document.getElementById("addKeyProjectForm").reset();
        document.getElementById("addIsActive").checked = true;
        const addSlidesContainerReset = document.getElementById("addProjectSlidesContainer");
        if (addSlidesContainerReset) addSlidesContainerReset.innerHTML = "";
        loadKeyProjects(currentPage);
    } catch (err) {
        console.error(err);
        window.notify(err.message || "Failed to add key project", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

async function updateKeyProject(projectId, suffix) {
    const button = document.getElementById(`editProjectBtn_${projectId}`);
    setButtonLoading(button, true);
    try {
        const formData = new FormData();
        formData.append("title", JSON.stringify(getTitles("edit", suffix)));
        formData.append("description", JSON.stringify(getDescriptions("edit", suffix)));

        const imageInput = document.getElementById(`editImageFile${suffix}`);
        if (imageInput?.files?.[0]) {
            formData.append("image_file", imageInput.files[0]);
        }

        formData.append("stack", document.getElementById(`editStack${suffix}`).value.trim());
        formData.append("status", document.getElementById(`editStatus${suffix}`).value);
        formData.append("sort_order", document.getElementById(`editSortOrder${suffix}`).value || "0");
        formData.append("demo_url", document.getElementById(`editDemoUrl${suffix}`).value.trim());
        formData.append("repo_url", document.getElementById(`editRepoUrl${suffix}`).value.trim());
        formData.append("is_active", document.getElementById(`editIsActive${suffix}`).checked ? "true" : "false");
        const editSlidesContainer = document.getElementById(`editProjectSlidesContainer${suffix}`);
        formData.append("slides_meta", JSON.stringify(serializeSlideRows(editSlidesContainer, formData)));

        const result = await adminKeyProjectService.update(projectId, formData);
        if (!result.ok) throw new Error(result.data?.message || "Failed to update project");

        window.notify(result.data?.message || "Updated", "success");
        const modalEl = button.closest(".modal");
        bootstrap.Modal.getInstance(modalEl)?.hide();
        loadKeyProjects(currentPage);
    } catch (err) {
        console.error(err);
        window.notify(err.message || "Failed to update key project", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

async function deleteKeyProject(projectId, modalId) {
    const button = document.getElementById(`deleteProjectBtn_${projectId}`);
    setButtonLoading(button, true);
    try {
        const result = await adminKeyProjectService.remove(projectId);
        if (!result.ok) throw new Error(result.data?.message || "Failed to delete project");

        window.notify(result.data?.message || "Deleted", "success");
        const modalEl = document.getElementById(modalId);
        bootstrap.Modal.getInstance(modalEl)?.hide();
        loadKeyProjects(currentPage);
    } catch (err) {
        console.error(err);
        window.notify(err.message || "Failed to delete key project", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const perPageSelect = document.getElementById("perPageSelect");
    const searchInput = document.getElementById("searchInput");
    const orderSelect = document.getElementById("orderSelect");
    const statusFilterSelect = document.getElementById("statusFilterSelect");
    const activeFilterSelect = document.getElementById("activeFilterSelect");

    perPageSelect?.addEventListener("change", () => {
        perPage = Number(perPageSelect.value || 10);
        currentPage = 1;
        loadKeyProjects(currentPage);
    });

    searchInput?.addEventListener("input", (event) => {
        const nextValue = String(event.target.value || "").trim();
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            searchQuery = nextValue;
            currentPage = 1;
            loadKeyProjects(currentPage);
        }, 300);
    });

    orderSelect?.addEventListener("change", (event) => {
        sortOrder = String(event.target.value || "asc");
        currentPage = 1;
        loadKeyProjects(currentPage);
    });

    statusFilterSelect?.addEventListener("change", (event) => {
        statusFilter = String(event.target.value || "").trim();
        currentPage = 1;
        loadKeyProjects(currentPage);
    });

    activeFilterSelect?.addEventListener("change", (event) => {
        activeFilter = String(event.target.value || "").trim();
        currentPage = 1;
        loadKeyProjects(currentPage);
    });

    document.getElementById("prevPage")?.addEventListener("click", () => {
        if (currentPage <= 1) return;
        currentPage -= 1;
        loadKeyProjects(currentPage);
    });

    document.getElementById("nextPage")?.addEventListener("click", () => {
        currentPage += 1;
        loadKeyProjects(currentPage);
    });

    document.addEventListener("click", (event) => {
        const addBtn = event.target.closest("[data-add-slide-row]");
        if (addBtn) {
            const targetSelector = addBtn.getAttribute("data-target");
            if (targetSelector) appendSlideRow(targetSelector);
            return;
        }

        const removeBtn = event.target.closest("[data-remove-slide-row]");
        if (removeBtn) {
            removeBtn.closest("[data-slide-row]")?.remove();
        }
    });

    loadKeyProjects(currentPage);
});

window.addKeyProject = addKeyProject;
window.updateKeyProject = updateKeyProject;
window.deleteKeyProject = deleteKeyProject;
window.playKeyProjectPreview = playKeyProjectPreview;

