import { AdminCrudService } from "../../services/AdminCrudService.js";

const adminBuiltAppService = new AdminCrudService("built-app");

let currentPage = 1;
let perPage = 10;
let searchQuery = "";
let sortOrder = "asc";
let platformFilter = "";
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

function getLocalizedMap(baseId, suffix = "") {
    const get = (localeKey) => document.getElementById(`${baseId}${localeKey}${suffix}`);
    return {
        en: get("En")?.value.trim() || "",
        ceb: get("Ceb")?.value.trim() || "",
        fr: get("Fr")?.value.trim() || "",
        fil_PH: get("Fil")?.value.trim() || "",
    };
}

function setLocalizedValues(map) {
    return {
        en: (map && map.en) || "",
        ceb: (map && map.ceb) || "",
        fr: (map && map.fr) || "",
        fil_PH: (map && map.fil_PH) || "",
    };
}

function splitParagraphs(text) {
    return String(text || "")
        .split(/\n\s*\n|\r\n\s*\r\n/)
        .map((p) => p.trim())
        .filter(Boolean);
}

function platformBadge(platform) {
    const color = String(platform).toLowerCase() === "mobile" ? "primary" : "dark";
    return `<span class="badge text-bg-${color}">${escapeHtml(platform || "Mobile")}</span>`;
}

function buildSnapshotRowMarkup(snapshot = {}) {
    const imageUrl = snapshot.image_url || "";
    const snapshotId = snapshot.id || "";

    return `
    <div class="app-snapshot-row border rounded p-2" data-snapshot-row data-snapshot-id="${escapeHtml(snapshotId)}">
      <div class="row g-2 align-items-start">
        <div class="col-md-4">
          ${imageUrl ? `<div class="mb-1"><img src="${escapeHtml(imageUrl)}" alt="Snapshot preview" style="width:100%;max-height:90px;object-fit:cover;border-radius:6px;border:1px solid #ddd;"></div>` : ""}
          <input type="file" class="form-control form-control-sm" accept="image/*" data-snapshot-file>
          <div class="form-text">${imageUrl ? "Upload to replace this snapshot." : "Upload snapshot image."}</div>
        </div>
        <div class="col-md-8 d-flex align-items-end justify-content-end">
          <button type="button" class="btn btn-outline-danger btn-sm" data-remove-snapshot-row title="Remove snapshot">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    </div>`;
}

function serializeSnapshotRows(container, formData) {
    if (!container) return [];

    const rows = Array.from(container.querySelectorAll("[data-snapshot-row]"));
    const snapshotsMeta = [];

    rows.forEach((row, index) => {
        const fileInput = row.querySelector("[data-snapshot-file]");
        const snapshotId = row.dataset.snapshotId || "";

        let imageField = "";
        const file = fileInput?.files?.[0];
        if (file) {
            imageField = `snapshot_file_${Date.now()}_${index}_${Math.random().toString(36).slice(2, 8)}`;
            formData.append(imageField, file);
        }

        if (!imageField && !snapshotId) return;

        snapshotsMeta.push({
            id: snapshotId || null,
            image_field: imageField,
            sort_order: index,
        });
    });

    return snapshotsMeta;
}

async function loadBuiltApps(page = 1) {
    const tbody = document.getElementById("builtAppsTableBody");
    const modalContainer = document.getElementById("builtAppModals");
    const pageInfo = document.getElementById("pageInfo");

    tbody.innerHTML = `<tr><td colspan="9" class="text-center">Loading...</td></tr>`;
    modalContainer.innerHTML = "";

    try {
        const data = await adminBuiltAppService.fetchList({
            page,
            perPage,
            order: sortOrder,
            search: searchQuery,
            platform: platformFilter,
            is_active: activeFilter,
        });
        const rows = data.apps || [];

        tbody.innerHTML = "";

        if (!rows.length) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center">No built apps found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages || 1}`;
            document.getElementById("prevPage").disabled = true;
            document.getElementById("nextPage").disabled = true;
            return;
        }

        rows.forEach((app, index) => {
            const rowNo = (page - 1) * perPage + index + 1;
            const editModalId = `editAppModal_${page}_${index}`;
            const safeName = escapeHtml(app.name?.en || app.slug || "Untitled");
            const safeSlug = escapeHtml(app.slug || "");
            const snapshotCount = Array.isArray(app.snapshots) ? app.snapshots.length : 0;

            tbody.insertAdjacentHTML("beforeend", `
                <tr>
                    <td>${rowNo}</td>
                    <td>
                        <div style="max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${safeName}">
                            ${safeName}
                        </div>
                    </td>
                    <td><code>${safeSlug}</code></td>
                    <td>${platformBadge(app.platform)}</td>
                    <td>${escapeHtml(app.version || "-")}</td>
                    <td><span class="badge text-bg-info">${snapshotCount}</span></td>
                    <td>${Number(app.sort_order || 0)}</td>
                    <td>${app.is_active === false ? '<span class="badge text-bg-secondary">No</span>' : '<span class="badge text-bg-success">Yes</span>'}</td>
                    <td>
                        <div class="ba-admin-actions">
                            <a class="btn btn-sm btn-outline-secondary" href="/apps/${safeSlug}" target="_blank" rel="noopener" title="View public page">
                                <i class="bi bi-eye"></i>
                            </a>
                            <button class="btn btn-sm btn-primary me-1" data-bs-toggle="modal" data-bs-target="#${editModalId}">
                                <i class="bi bi-pencil"></i> Edit
                            </button>
                            <button class="btn btn-sm btn-danger built-app-delete-btn"
                                data-record-id="${app._id}"
                                data-name="${safeName}">
                                <i class="bi bi-trash"></i> Delete
                            </button>
                        </div>
                    </td>
                </tr>
            `);

            modalContainer.insertAdjacentHTML("beforeend", buildEditModal(app, editModalId, page, index));
        });

        pageInfo.textContent = `Page ${page} | ${data.total_pages || 1}`;
        document.getElementById("prevPage").disabled = page <= 1;
        document.getElementById("nextPage").disabled = page >= (data.total_pages || 1);

        tbody.querySelectorAll(".built-app-delete-btn").forEach((btn) => {
            btn.addEventListener("click", function () {
                const recordId = this.dataset.recordId;
                const name = this.dataset.name;
                window.confirmDelete(
                    `Are you sure you want to delete <strong>${name}</strong>? Its snapshots will also be removed.`,
                    async () => {
                        const result = await adminBuiltAppService.remove(recordId);
                        if (!result.ok) throw new Error(result.data?.message || "Failed to delete app");
                        bootstrap.Modal.getInstance(document.getElementById("deleteConfirmModal")).hide();
                        window.notify(result.data?.message || "Deleted", "success");
                        loadBuiltApps(currentPage);
                    }
                );
            });
        });
    } catch (error) {
        console.error(error);
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">Error loading built apps</td></tr>`;
    }
}

function toggleBuiltAppModalMaximize(btn) {
    const modalId = btn.dataset.targetModal || btn.closest(".modal")?.id;
    if (!modalId) return;
    const dialog = document.querySelector("#" + modalId + " .modal-dialog");
    const modalBody = dialog?.querySelector(".modal-body");
    if (!dialog) return;
    dialog.classList.toggle("modal-fullscreen");
    const isFull = dialog.classList.contains("modal-fullscreen");

    if (modalBody) {
        modalBody.style.maxHeight = isFull ? "calc(100vh - 120px)" : "";
    }

    btn.innerHTML = isFull
        ? '<i class="bi bi-fullscreen-exit"></i>'
        : '<i class="bi bi-arrows-fullscreen"></i>';
    btn.setAttribute("title", isFull ? "Restore" : "Maximize");
    btn.setAttribute("aria-label", isFull ? "Restore" : "Maximize");
}

function buildEditModal(app, modalId, page, index) {
    const suffix = `_${page}_${index}`;
    const name = setLocalizedValues(app.name || {});
    const shortDescription = setLocalizedValues(app.short_description || {});
    const fullDescription = app.full_description || {};
    const toText = (list) => Array.isArray(list) ? list.join("\n\n") : "";
    const fullEn = toText(fullDescription.en);
    const fullCeb = toText(fullDescription.ceb);
    const fullFr = toText(fullDescription.fr);
    const fullFil = toText(fullDescription.fil_PH);
    const snapshots = Array.isArray(app.snapshots) ? app.snapshots : [];
    const snapshotsMarkup = snapshots.map((s) => buildSnapshotRowMarkup(s)).join("");

    return `
    <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title me-auto">Edit Built App</h5>
            <div class="d-flex align-items-center gap-1">
              <button type="button" class="btn p-1 preview-header-btn edit-maximize-btn" data-target-modal="${modalId}" aria-label="Maximize" title="Maximize">
                <i class="bi bi-arrows-fullscreen"></i>
              </button>
              <button type="button" class="btn p-1 preview-header-btn" data-bs-dismiss="modal" aria-label="Close">
                <i class="bi bi-x-lg"></i>
              </button>
            </div>
          </div>
          <div class="modal-body">
            <form id="editAppForm${suffix}">
              <div class="row g-3">
                <div class="col-md-6"><label class="form-label">Name (EN)</label><input type="text" id="editNameEn${suffix}" class="form-control" value="${escapeHtml(name.en)}" required></div>
                <div class="col-md-6"><label class="form-label">Name (Ceb)</label><input type="text" id="editNameCeb${suffix}" class="form-control" value="${escapeHtml(name.ceb)}"></div>
                <div class="col-md-6"><label class="form-label">Name (Fr)</label><input type="text" id="editNameFr${suffix}" class="form-control" value="${escapeHtml(name.fr)}"></div>
                <div class="col-md-6"><label class="form-label">Name (Fil)</label><input type="text" id="editNameFil${suffix}" class="form-control" value="${escapeHtml(name.fil_PH)}"></div>

                <div class="col-md-3"><label class="form-label">Slug</label><input type="text" id="editSlug${suffix}" class="form-control" value="${escapeHtml(app.slug || "")}"></div>
                <div class="col-md-3">
                  <label class="form-label">Platform</label>
                  <select id="editPlatform${suffix}" class="form-select">
                    <option value="Mobile" ${app.platform === "Mobile" ? "selected" : ""}>Mobile</option>
                    <option value="Desktop" ${app.platform === "Desktop" ? "selected" : ""}>Desktop</option>
                  </select>
                </div>
                <div class="col-md-3"><label class="form-label">Version</label><input type="text" id="editVersion${suffix}" class="form-control" value="${escapeHtml(app.version || "")}"></div>
                <div class="col-md-3"><label class="form-label">Sort Order</label><input type="number" id="editSortOrder${suffix}" class="form-control" value="${Number(app.sort_order || 0)}"></div>

                <div class="col-md-6"><label class="form-label">Icon (ion-icon name)</label><input type="text" id="editIcon${suffix}" class="form-control" value="${escapeHtml(app.icon || "")}"></div>
                <div class="col-md-6"><label class="form-label">Download URL</label><input type="url" id="editDownloadUrl${suffix}" class="form-control" value="${escapeHtml(app.download_url || "")}"></div>

                <div class="col-12"><label class="form-label">Short Description (EN)</label><textarea id="editShortEn${suffix}" class="form-control" rows="2">${escapeHtml(shortDescription.en)}</textarea></div>
                <div class="col-md-4"><label class="form-label">Short Description (Ceb)</label><textarea id="editShortCeb${suffix}" class="form-control" rows="2">${escapeHtml(shortDescription.ceb)}</textarea></div>
                <div class="col-md-4"><label class="form-label">Short Description (Fr)</label><textarea id="editShortFr${suffix}" class="form-control" rows="2">${escapeHtml(shortDescription.fr)}</textarea></div>
                <div class="col-md-4"><label class="form-label">Short Description (Fil)</label><textarea id="editShortFil${suffix}" class="form-control" rows="2">${escapeHtml(shortDescription.fil_PH)}</textarea></div>

                <div class="col-12"><label class="form-label">Full Description (EN)</label><textarea id="editFullEn${suffix}" class="form-control" rows="4">${escapeHtml(fullEn)}</textarea></div>
                <div class="col-md-4"><label class="form-label">Full Description (Ceb)</label><textarea id="editFullCeb${suffix}" class="form-control" rows="4">${escapeHtml(fullCeb)}</textarea></div>
                <div class="col-md-4"><label class="form-label">Full Description (Fr)</label><textarea id="editFullFr${suffix}" class="form-control" rows="4">${escapeHtml(fullFr)}</textarea></div>
                <div class="col-md-4"><label class="form-label">Full Description (Fil)</label><textarea id="editFullFil${suffix}" class="form-control" rows="4">${escapeHtml(fullFil)}</textarea></div>

                <div class="col-12">
                  <div class="card border">
                    <div class="card-header d-flex justify-content-between align-items-center">
                      <strong>Snapshots</strong>
                      <button type="button" class="btn btn-sm btn-outline-primary" data-add-snapshot-row data-target="#editSnapshotsContainer${suffix}">
                        <i class="bi bi-plus"></i> Add Snapshot
                      </button>
                    </div>
                    <div class="card-body">
                      <p class="text-muted small mb-2">Removing a row deletes its image from Cloudinary on save.</p>
                      <div id="editSnapshotsContainer${suffix}" class="d-grid gap-2">${snapshotsMarkup}</div>
                    </div>
                  </div>
                </div>

                <div class="col-12 form-check mt-2 ms-2">
                  <input class="form-check-input" type="checkbox" id="editIsActive${suffix}" ${app.is_active === false ? "" : "checked"}>
                  <label class="form-check-label" for="editIsActive${suffix}">Active (show on portfolio)</label>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-primary" id="editAppBtn_${app._id}"
              data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Saving...'
              onclick="updateBuiltApp('${app._id}', '${suffix}')">Save changes</button>
          </div>
        </div>
      </div>
    </div>`;
}

async function addBuiltApp() {
    const button = document.getElementById("addAppBtn");
    setButtonLoading(button, true);

    try {
        const names = getLocalizedMap("addName");
        if (!names.en) {
            window.notify("English name is required.", "warning");
            return;
        }

        const formData = new FormData();
        formData.append("name", JSON.stringify(names));
        formData.append("short_description", JSON.stringify(getLocalizedMap("addShort")));
        formData.append("full_description", JSON.stringify({
            en: splitParagraphs(document.getElementById("addFullEn").value),
            ceb: splitParagraphs(document.getElementById("addFullCeb").value),
            fr: splitParagraphs(document.getElementById("addFullFr").value),
            fil_PH: splitParagraphs(document.getElementById("addFullFil").value),
        }));
        formData.append("platform", document.getElementById("addPlatform").value);
        formData.append("version", document.getElementById("addVersion").value.trim());
        formData.append("icon", document.getElementById("addIcon").value.trim());
        formData.append("download_url", document.getElementById("addDownloadUrl").value.trim());
        formData.append("sort_order", document.getElementById("addSortOrder").value || "0");
        formData.append("is_active", document.getElementById("addIsActive").checked ? "true" : "false");

        const filesInput = document.getElementById("addSnapshotFiles");
        Array.from(filesInput?.files || []).forEach((file) => formData.append("snapshot_files", file));

        const result = await adminBuiltAppService.add(formData);
        if (!result.ok) throw new Error(result.data?.message || "Failed to add app");

        window.notify(result.data?.message || "Added", "success");
        const modalEl = document.getElementById("addAppModal");
        bootstrap.Modal.getInstance(modalEl)?.hide();
        document.getElementById("addBuiltAppForm").reset();
        document.getElementById("addIsActive").checked = true;
        loadBuiltApps(currentPage);
    } catch (err) {
        console.error(err);
        window.notify(err.message || "Failed to add built app", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

async function updateBuiltApp(appId, suffix) {
    const button = document.getElementById(`editAppBtn_${appId}`);
    setButtonLoading(button, true);
    try {
        const formData = new FormData();
        formData.append("name", JSON.stringify(getLocalizedMap("editName", suffix)));
        formData.append("short_description", JSON.stringify(getLocalizedMap("editShort", suffix)));
        formData.append("full_description", JSON.stringify({
            en: splitParagraphs(document.getElementById(`editFullEn${suffix}`).value),
            ceb: splitParagraphs(document.getElementById(`editFullCeb${suffix}`).value),
            fr: splitParagraphs(document.getElementById(`editFullFr${suffix}`).value),
            fil_PH: splitParagraphs(document.getElementById(`editFullFil${suffix}`).value),
        }));
        formData.append("slug", document.getElementById(`editSlug${suffix}`).value.trim());
        formData.append("platform", document.getElementById(`editPlatform${suffix}`).value);
        formData.append("version", document.getElementById(`editVersion${suffix}`).value.trim());
        formData.append("icon", document.getElementById(`editIcon${suffix}`).value.trim());
        formData.append("download_url", document.getElementById(`editDownloadUrl${suffix}`).value.trim());
        formData.append("sort_order", document.getElementById(`editSortOrder${suffix}`).value || "0");
        formData.append("is_active", document.getElementById(`editIsActive${suffix}`).checked ? "true" : "false");

        const editContainer = document.getElementById(`editSnapshotsContainer${suffix}`);
        formData.append("snapshots_meta", JSON.stringify(serializeSnapshotRows(editContainer, formData)));

        const result = await adminBuiltAppService.update(appId, formData);
        if (!result.ok) throw new Error(result.data?.message || "Failed to update app");

        window.notify(result.data?.message || "Updated", "success");
        const modalEl = button.closest(".modal");
        bootstrap.Modal.getInstance(modalEl)?.hide();
        loadBuiltApps(currentPage);
    } catch (err) {
        console.error(err);
        window.notify(err.message || "Failed to update built app", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const addMaxBtn = document.getElementById("addBuiltAppMaximizeBtn");
    if (addMaxBtn) {
        addMaxBtn.dataset.targetModal = "addAppModal";
        addMaxBtn.addEventListener("click", function () {
            toggleBuiltAppModalMaximize(this);
        });
    }

    document.addEventListener("click", function (e) {
        const maxBtn = e.target.closest(".edit-maximize-btn");
        if (maxBtn) {
            const modalId = maxBtn.dataset.targetModal;
            if (modalId) toggleBuiltAppModalMaximize(maxBtn);
            return;
        }

        const addRowBtn = e.target.closest("[data-add-snapshot-row]");
        if (addRowBtn) {
            const targetSelector = addRowBtn.getAttribute("data-target");
            const container = targetSelector ? document.querySelector(targetSelector) : null;
            container?.insertAdjacentHTML("beforeend", buildSnapshotRowMarkup({}));
            return;
        }

        const removeRowBtn = e.target.closest("[data-remove-snapshot-row]");
        if (removeRowBtn) {
            removeRowBtn.closest("[data-snapshot-row]")?.remove();
        }
    });

    const perPageSelect = document.getElementById("perPageSelect");
    const searchInput = document.getElementById("searchInput");
    const orderSelect = document.getElementById("orderSelect");
    const platformFilterSelect = document.getElementById("platformFilterSelect");
    const activeFilterSelect = document.getElementById("activeFilterSelect");

    perPageSelect?.addEventListener("change", () => {
        perPage = Number(perPageSelect.value || 10);
        currentPage = 1;
        loadBuiltApps(currentPage);
    });

    searchInput?.addEventListener("input", (event) => {
        const nextValue = String(event.target.value || "").trim();
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            searchQuery = nextValue;
            currentPage = 1;
            loadBuiltApps(currentPage);
        }, 300);
    });

    orderSelect?.addEventListener("change", (event) => {
        sortOrder = String(event.target.value || "asc");
        currentPage = 1;
        loadBuiltApps(currentPage);
    });

    platformFilterSelect?.addEventListener("change", (event) => {
        platformFilter = String(event.target.value || "").trim();
        currentPage = 1;
        loadBuiltApps(currentPage);
    });

    activeFilterSelect?.addEventListener("change", (event) => {
        activeFilter = String(event.target.value || "").trim();
        currentPage = 1;
        loadBuiltApps(currentPage);
    });

    document.getElementById("prevPage")?.addEventListener("click", () => {
        if (currentPage <= 1) return;
        currentPage -= 1;
        loadBuiltApps(currentPage);
    });

    document.getElementById("nextPage")?.addEventListener("click", () => {
        currentPage += 1;
        loadBuiltApps(currentPage);
    });

    loadBuiltApps(currentPage);
});

window.addBuiltApp = addBuiltApp;
window.updateBuiltApp = updateBuiltApp;
