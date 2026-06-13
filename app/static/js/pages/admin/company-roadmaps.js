import { AdminCrudService } from "../../services/AdminCrudService.js";

const adminCompanyRoadmapService = new AdminCrudService("company-roadmap");

let currentPage = 1;
let perPage = 10;
let searchQuery = "";
let sortOrder = "asc";
let employmentTypeFilter = "";
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

function normalizeI18nTextMap(value, fallbackEn = "") {
    const base = { en: "", ceb: "", fil_PH: "" };
    if (value && typeof value === "object" && !Array.isArray(value)) {
        base.en = String(value.en || "").trim();
        base.ceb = String(value.ceb || "").trim();
        base.fil_PH = String(value.fil_PH || "").trim();
    }
    if (!base.en && fallbackEn) {
        base.en = String(fallbackEn).trim();
    }
    return base;
}

function normalizeI18nHighlightsMap(value, fallbackEn = []) {
    const base = { en: [], ceb: [], fil_PH: [] };
    const coerceList = (input) => {
        if (Array.isArray(input)) return input.map((x) => String(x || "").trim()).filter(Boolean);
        if (typeof input === "string") return input.split("\n").map((x) => x.trim()).filter(Boolean);
        return [];
    };

    if (value && typeof value === "object" && !Array.isArray(value)) {
        base.en = coerceList(value.en);
        base.ceb = coerceList(value.ceb);
        base.fil_PH = coerceList(value.fil_PH);
    }

    if (!base.en.length) {
        base.en = coerceList(fallbackEn);
    }

    return base;
}

function buildActivityRowMarkup(activity = {}) {
    const imageUrl = activity.image_url || "";
    const title = activity.title || "";
    const caption = activity.caption || "";
    const activityId = activity.id || "";
    const titleI18n = normalizeI18nTextMap(activity.title_i18n, title);
    const captionI18n = normalizeI18nTextMap(activity.caption_i18n, caption);

    return `
    <div class="activity-row-card" data-activity-row data-activity-id="${escapeHtml(activityId)}" data-existing-image-url="${escapeHtml(imageUrl)}">
      <div class="row g-2 align-items-start">
        <div class="col-md-3">
          <label class="form-label mb-1">Image</label>
          ${imageUrl ? `<div class="mb-2"><img src="${escapeHtml(imageUrl)}" alt="Activity preview" style="width:100%;max-height:90px;object-fit:cover;border-radius:6px;border:1px solid #ddd;"></div>` : ""}
          <input type="file" class="form-control form-control-sm" accept="image/*" data-activity-file>
          <div class="form-text">Upload to add/replace image.</div>
        </div>
        <div class="col-md-3">
          <label class="form-label mb-1">Title</label>
          <input type="text" class="form-control form-control-sm" value="${escapeHtml(title)}" data-activity-title placeholder="Team Collaboration">
        </div>
        <div class="col-md-5">
          <label class="form-label mb-1">Caption</label>
          <textarea class="form-control form-control-sm" rows="3" data-activity-caption placeholder="Short context about the activity image">${escapeHtml(caption)}</textarea>
        </div>
        <div class="col-md-1 d-grid">
          <label class="form-label mb-1">&nbsp;</label>
          <button type="button" class="btn btn-outline-danger btn-sm" data-remove-activity-row title="Remove activity image">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
      <div class="row g-2 mt-1">
        <div class="col-md-6">
          <label class="form-label mb-1">Title (Cebuano)</label>
          <input type="text" class="form-control form-control-sm" value="${escapeHtml(titleI18n.ceb)}" data-activity-title-ceb placeholder="Optional translation">
        </div>
        <div class="col-md-6">
          <label class="form-label mb-1">Title (Tagalog)</label>
          <input type="text" class="form-control form-control-sm" value="${escapeHtml(titleI18n.fil_PH)}" data-activity-title-fil placeholder="Optional translation">
        </div>
        <div class="col-md-6">
          <label class="form-label mb-1">Caption (Cebuano)</label>
          <textarea class="form-control form-control-sm" rows="2" data-activity-caption-ceb placeholder="Optional translation">${escapeHtml(captionI18n.ceb)}</textarea>
        </div>
        <div class="col-md-6">
          <label class="form-label mb-1">Caption (Tagalog)</label>
          <textarea class="form-control form-control-sm" rows="2" data-activity-caption-fil placeholder="Optional translation">${escapeHtml(captionI18n.fil_PH)}</textarea>
        </div>
      </div>
    </div>`;
}

function appendActivityRow(containerSelector, activity = {}) {
    const container = typeof containerSelector === "string"
        ? document.querySelector(containerSelector)
        : containerSelector;
    if (!container) return;
    container.insertAdjacentHTML("beforeend", buildActivityRowMarkup(activity));
}

function serializeActivityRows(container, formData) {
    if (!container) return [];
    const rows = Array.from(container.querySelectorAll("[data-activity-row]"));
    const activitiesMeta = [];

    rows.forEach((row, index) => {
        const fileInput = row.querySelector("[data-activity-file]");
        const titleInput = row.querySelector("[data-activity-title]");
        const captionInput = row.querySelector("[data-activity-caption]");
        const titleCebInput = row.querySelector("[data-activity-title-ceb]");
        const titleFilInput = row.querySelector("[data-activity-title-fil]");
        const captionCebInput = row.querySelector("[data-activity-caption-ceb]");
        const captionFilInput = row.querySelector("[data-activity-caption-fil]");

        const title = (titleInput?.value || "").trim();
        const caption = (captionInput?.value || "").trim();
        const titleCeb = (titleCebInput?.value || "").trim();
        const titleFil = (titleFilInput?.value || "").trim();
        const captionCeb = (captionCebInput?.value || "").trim();
        const captionFil = (captionFilInput?.value || "").trim();
        const existingImageUrl = row.dataset.existingImageUrl || "";
        const activityId = row.dataset.activityId || "";

        let imageField = "";
        const file = fileInput?.files?.[0];
        if (file) {
            imageField = `activity_file_${Date.now()}_${index}_${Math.random().toString(36).slice(2, 8)}`;
            formData.append(imageField, file);
        }

        if (!imageField && !existingImageUrl) {
            if (!title && !caption) return;
            throw new Error(`Activity image ${index + 1}: image is required.`);
        }

        activitiesMeta.push({
            id: activityId || null,
            image_field: imageField,
            existing_image_url: existingImageUrl || null,
            title,
            caption,
            title_i18n: {
                en: title,
                ceb: titleCeb,
                fil_PH: titleFil,
            },
            caption_i18n: {
                en: caption,
                ceb: captionCeb,
                fil_PH: captionFil,
            },
            sort_order: index,
        });
    });

    return activitiesMeta;
}

function buildActionsCell(editModalId, recordId, companyName, roleTitle) {
    return `
    <div class="company-roadmap-actions">
      <button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#${editModalId}">
        <i class="bi bi-pencil"></i> Edit
      </button>
      <button class="btn btn-sm btn-danger company-roadmap-delete-btn"
        data-record-id="${recordId}"
        data-company="${escapeHtml(companyName || "")}"
        data-role="${escapeHtml(roleTitle || "")}">
        <i class="bi bi-trash"></i> Delete
      </button>
    </div>`;
}

async function loadCompanyRoadmaps(page = 1) {
    const tbody = document.getElementById("companyRoadmapsTableBody");
    const modalContainer = document.getElementById("companyRoadmapModals");
    const pageInfo = document.getElementById("pageInfo");

    tbody.innerHTML = `<tr><td colspan="9" class="text-center">Loading...</td></tr>`;
    modalContainer.innerHTML = "";

    try {
        const data = await adminCompanyRoadmapService.fetchList({
            page,
            perPage,
            order: sortOrder,
            search: searchQuery,
            employment_type: employmentTypeFilter,
            is_active: activeFilter,
        });
        const rows = data.roadmaps || [];

        tbody.innerHTML = "";

        if (!rows.length) {
            tbody.innerHTML = `<tr><td colspan="9" class="text-center">No company roadmap entries found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages || 1}`;
            document.getElementById("prevPage").disabled = true;
            document.getElementById("nextPage").disabled = true;
            return;
        }

        rows.forEach((entry, index) => {
            const rowNo = (page - 1) * perPage + index + 1;
            const editModalId = `editRoadmapModal_${page}_${index}`;
            const deleteModalId = `deleteRoadmapModal_${page}_${index}`;
            const cover = entry.cover_image_url || "";
            const activitiesCount = Array.isArray(entry.activities) ? entry.activities.length : 0;

            tbody.insertAdjacentHTML("beforeend", `
                <tr>
                  <td>${rowNo}</td>
                  <td style="width:92px;">
                    ${cover ? `<img
                      src="${escapeHtml(cover)}"
                      alt="${escapeHtml(entry.company_name || "")}"
                      data-preview-src="${escapeHtml(cover)}"
                      data-preview-title="${escapeHtml(entry.company_name || "Company Roadmap")}"
                      onclick="playCompanyRoadmapPreview(this.dataset.previewSrc, this.dataset.previewTitle)"
                      style="cursor:pointer;width:64px;height:48px;object-fit:cover;border-radius:6px;border:1px solid #ddd;">` : `<span class="text-muted">No image</span>`}
                  </td>
                  <td>
                    <div class="company-roadmap-summary" style="max-width:220px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${escapeHtml(entry.company_name || "")}">
                      ${escapeHtml(entry.company_name || "-")}
                    </div>
                  </td>
                  <td>${escapeHtml(entry.role_title || "-")}</td>
                  <td>${escapeHtml(entry.period || "-")}</td>
                  <td><span class="badge text-bg-light border">${escapeHtml(entry.employment_type || "Experience")}</span></td>
                  <td><span class="badge text-bg-info">${activitiesCount}</span></td>
                  <td>${entry.is_active === false ? '<span class="badge text-bg-secondary">No</span>' : '<span class="badge text-bg-success">Yes</span>'}</td>
                  <td>${buildActionsCell(editModalId, entry._id, entry.company_name, entry.role_title)}</td>
                </tr>
            `);

            modalContainer.insertAdjacentHTML("beforeend", buildEditModal(entry, editModalId, page, index));
        });

        pageInfo.textContent = `Page ${page} | ${data.total_pages || 1}`;
        document.getElementById("prevPage").disabled = page <= 1;
        document.getElementById("nextPage").disabled = page >= (data.total_pages || 1);

        // Attach delete handlers via delegation
        tbody.querySelectorAll(".company-roadmap-delete-btn").forEach((btn) => {
            btn.addEventListener("click", function () {
                const recordId = this.dataset.recordId;
                const company = this.dataset.company;
                const role = this.dataset.role;
                window.confirmDelete(
                    `Are you sure you want to delete <strong>${company}</strong>${role ? ` (${role})` : ""}?`,
                    async () => {
                        const result = await adminCompanyRoadmapService.remove(recordId);
                        if (!result.ok) throw new Error(result.data?.message || "Failed to delete entry");
                        bootstrap.Modal.getInstance(document.getElementById("deleteConfirmModal")).hide();
                        window.notify(result.data?.message || "Deleted", "success");
                        loadCompanyRoadmaps(currentPage);
                    }
                );
            });
        });
    } catch (error) {
        console.error(error);
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">Error loading company roadmap entries</td></tr>`;
    }
}

function playCompanyRoadmapPreview(url, title = "Company Roadmap Image") {
    if (typeof window.openAdminImagePreview !== "function") {
        console.error("openAdminImagePreview is not available.");
        return;
    }
    window.openAdminImagePreview(url, title || "Company Roadmap Image");
}

function buildEditModal(entry, modalId, page, index) {
    const suffix = `_${page}_${index}`;
    const activities = Array.isArray(entry.activities) ? entry.activities : [];
    const activitiesMarkup = activities.map((a) => buildActivityRowMarkup(a)).join("");
    const roleTitleI18n = normalizeI18nTextMap(entry.role_title_i18n, entry.role_title || "");
    const definitionI18n = normalizeI18nTextMap(entry.definition_i18n, entry.definition || "");
    const summaryI18n = normalizeI18nTextMap(entry.summary_i18n, entry.summary || "");
    const highlightsI18n = normalizeI18nHighlightsMap(entry.highlights_i18n, entry.highlights || []);
    const highlights = highlightsI18n.en.join("\n");
    const highlightsCeb = highlightsI18n.ceb.join("\n");
    const highlightsFil = highlightsI18n.fil_PH.join("\n");

    return `
    <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Company Roadmap Entry</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <form id="editRoadmapForm${suffix}">
              <div class="row g-3">
                <div class="col-md-6"><label class="form-label">Company Name</label><input type="text" id="editCompanyName${suffix}" class="form-control" value="${escapeHtml(entry.company_name || "")}"></div>
                <div class="col-md-6"><label class="form-label">Role Title</label><input type="text" id="editRoleTitle${suffix}" class="form-control" value="${escapeHtml(entry.role_title || "")}"></div>

                <div class="col-md-4"><label class="form-label">Period</label><input type="text" id="editPeriod${suffix}" class="form-control" value="${escapeHtml(entry.period || "")}"></div>
                <div class="col-md-4">
                  <label class="form-label">Employment Type</label>
                  <select id="editEmploymentType${suffix}" class="form-select">
                    ${["Internship", "Full-time", "Contract", "Freelance", "Experience"].map(type => `<option value="${type}" ${String(entry.employment_type || "") === type ? "selected" : ""}>${type}</option>`).join("")}
                  </select>
                </div>
                <div class="col-md-4"><label class="form-label">Location</label><input type="text" id="editLocation${suffix}" class="form-control" value="${escapeHtml(entry.location || "")}"></div>

                <div class="col-md-6"><label class="form-label">Definition</label><textarea id="editDefinition${suffix}" class="form-control" rows="3">${escapeHtml(entry.definition || "")}</textarea></div>
                <div class="col-md-6"><label class="form-label">Summary</label><textarea id="editSummary${suffix}" class="form-control" rows="3">${escapeHtml(entry.summary || "")}</textarea></div>

                <div class="col-md-6"><label class="form-label">Highlights (one per line)</label><textarea id="editHighlights${suffix}" class="form-control" rows="4">${escapeHtml(highlights)}</textarea></div>
                <div class="col-12">
                  <div class="card border">
                    <div class="card-header"><strong>Translations (Cebuano / Tagalog)</strong></div>
                    <div class="card-body">
                      <div class="row g-3">
                        <div class="col-md-6"><label class="form-label">Role Title (Cebuano)</label><input type="text" id="editRoleTitleCeb${suffix}" class="form-control" value="${escapeHtml(roleTitleI18n.ceb)}"></div>
                        <div class="col-md-6"><label class="form-label">Role Title (Tagalog)</label><input type="text" id="editRoleTitleFil${suffix}" class="form-control" value="${escapeHtml(roleTitleI18n.fil_PH)}"></div>
                        <div class="col-md-6"><label class="form-label">Definition (Cebuano)</label><textarea id="editDefinitionCeb${suffix}" class="form-control" rows="3">${escapeHtml(definitionI18n.ceb)}</textarea></div>
                        <div class="col-md-6"><label class="form-label">Definition (Tagalog)</label><textarea id="editDefinitionFil${suffix}" class="form-control" rows="3">${escapeHtml(definitionI18n.fil_PH)}</textarea></div>
                        <div class="col-md-6"><label class="form-label">Summary (Cebuano)</label><textarea id="editSummaryCeb${suffix}" class="form-control" rows="3">${escapeHtml(summaryI18n.ceb)}</textarea></div>
                        <div class="col-md-6"><label class="form-label">Summary (Tagalog)</label><textarea id="editSummaryFil${suffix}" class="form-control" rows="3">${escapeHtml(summaryI18n.fil_PH)}</textarea></div>
                        <div class="col-md-6"><label class="form-label">Highlights (Cebuano, one per line)</label><textarea id="editHighlightsCeb${suffix}" class="form-control" rows="4">${escapeHtml(highlightsCeb)}</textarea></div>
                        <div class="col-md-6"><label class="form-label">Highlights (Tagalog, one per line)</label><textarea id="editHighlightsFil${suffix}" class="form-control" rows="4">${escapeHtml(highlightsFil)}</textarea></div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="col-md-3"><label class="form-label">Accent Color</label><input type="color" id="editAccentColor${suffix}" class="form-control form-control-color" value="${escapeHtml(entry.accent_color || "#2962ff")}"></div>
                <div class="col-md-3"><label class="form-label">Sort Order</label><input type="number" id="editSortOrder${suffix}" class="form-control" value="${Number(entry.sort_order || 0)}"></div>

                <div class="col-md-6"><label class="form-label">Replace Cover Image (optional)</label><input type="file" id="editCoverImageFile${suffix}" class="form-control" accept="image/*"></div>
                <div class="col-md-6 d-flex align-items-end">
                  <div class="form-check ms-2 mb-2">
                    <input class="form-check-input" type="checkbox" id="editIsActive${suffix}" ${entry.is_active === false ? "" : "checked"}>
                    <label class="form-check-label" for="editIsActive${suffix}">Active (show on profile)</label>
                  </div>
                </div>

                <div class="col-12">
                  <div class="card border">
                    <div class="card-header d-flex justify-content-between align-items-center">
                      <strong>Activity Images</strong>
                      <button type="button" class="btn btn-sm btn-outline-primary" data-add-activity-row data-target="#editActivityRows${suffix}">
                        <i class="bi bi-plus"></i> Add Activity Image
                      </button>
                    </div>
                    <div class="card-body">
                      <div id="editActivityRows${suffix}" class="d-grid gap-2">${activitiesMarkup}</div>
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-primary" id="editRoadmapBtn_${entry._id}"
              data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Saving...'
              onclick="updateCompanyRoadmap('${entry._id}', '${suffix}')">Save changes</button>
          </div>
        </div>
      </div>
    </div>`;
}

function buildDeleteModal(entry, modalId) {
    return `
    <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Delete Company Roadmap Entry</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            Are you sure you want to delete <strong>${escapeHtml(entry.company_name || "this entry")}</strong> (${escapeHtml(entry.role_title || "")})?
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-danger" id="deleteRoadmapBtn_${entry._id}"
              data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Deleting...'
              onclick="deleteCompanyRoadmap('${entry._id}', '${modalId}')">Delete</button>
          </div>
        </div>
      </div>
    </div>`;
}

function collectRoadmapFormData(mode, suffix = "") {
    const formData = new FormData();
    const id = (base) => document.getElementById(`${mode}${base}${suffix}`);

    const companyName = id("CompanyName").value.trim();
    const roleTitle = id("RoleTitle").value.trim();
    const period = id("Period").value.trim();

    if (!companyName || !roleTitle || !period) {
        throw new Error("Company Name, Role Title, and Period are required.");
    }

    formData.append("company_name", companyName);
    formData.append("role_title", roleTitle);
    formData.append("period", period);
    formData.append("employment_type", id("EmploymentType").value);
    formData.append("location", id("Location").value.trim());
    formData.append("definition", id("Definition").value.trim());
    formData.append("summary", id("Summary").value.trim());
    formData.append("highlights", id("Highlights").value || "");
    formData.append("role_title_ceb", id("RoleTitleCeb")?.value?.trim() || "");
    formData.append("role_title_fil", id("RoleTitleFil")?.value?.trim() || "");
    formData.append("definition_ceb", id("DefinitionCeb")?.value?.trim() || "");
    formData.append("definition_fil", id("DefinitionFil")?.value?.trim() || "");
    formData.append("summary_ceb", id("SummaryCeb")?.value?.trim() || "");
    formData.append("summary_fil", id("SummaryFil")?.value?.trim() || "");
    formData.append("highlights_ceb", id("HighlightsCeb")?.value || "");
    formData.append("highlights_fil", id("HighlightsFil")?.value || "");
    formData.append("accent_color", id("AccentColor").value || "#2962ff");
    formData.append("sort_order", id("SortOrder").value || "0");
    formData.append("is_active", id("IsActive").checked ? "true" : "false");

    const coverFileInput = id("CoverImageFile");
    if (coverFileInput?.files?.[0]) {
        if (!coverFileInput.files[0].type.startsWith("image/")) {
            throw new Error("Please upload a valid cover image.");
        }
        formData.append("cover_image_file", coverFileInput.files[0]);
    }

    const activityContainer = document.getElementById(`${mode}ActivityRows${suffix}`);
    formData.append("activities_meta", JSON.stringify(serializeActivityRows(activityContainer, formData)));
    return formData;
}

async function addCompanyRoadmap() {
    const button = document.getElementById("addRoadmapBtn");
    setButtonLoading(button, true);

    try {
        const coverInput = document.getElementById("addCoverImageFile");
        if (!coverInput?.files?.[0]) {
            throw new Error("Cover image is required.");
        }

        const formData = collectRoadmapFormData("add");
        const result = await adminCompanyRoadmapService.add(formData);
        if (!result.ok) {
            throw new Error(result.data?.message || "Failed to add company roadmap entry.");
        }

        window.notify(result.data?.message || "Added", "success");
        const modalEl = document.getElementById("addRoadmapModal");
        bootstrap.Modal.getInstance(modalEl)?.hide();
        document.getElementById("addCompanyRoadmapForm").reset();
        document.getElementById("addAccentColor").value = "#2962ff";
        document.getElementById("addIsActive").checked = true;
        const addRows = document.getElementById("addActivityRows");
        if (addRows) addRows.innerHTML = "";
        loadCompanyRoadmaps(currentPage);
    } catch (error) {
        console.error(error);
        window.notify(error.message || "Failed to add company roadmap entry.", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

async function updateCompanyRoadmap(roadmapId, suffix) {
    const button = document.getElementById(`editRoadmapBtn_${roadmapId}`);
    setButtonLoading(button, true);

    try {
        const formData = collectRoadmapFormData("edit", suffix);
        const result = await adminCompanyRoadmapService.update(roadmapId, formData);
        if (!result.ok) {
            throw new Error(result.data?.message || "Failed to update company roadmap entry.");
        }

        window.notify(result.data?.message || "Updated", "success");
        const modalEl = button.closest(".modal");
        bootstrap.Modal.getInstance(modalEl)?.hide();
        loadCompanyRoadmaps(currentPage);
    } catch (error) {
        console.error(error);
        window.notify(error.message || "Failed to update company roadmap entry.", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

async function deleteCompanyRoadmap(roadmapId) {
    const result = await adminCompanyRoadmapService.remove(roadmapId);
    if (!result.ok) throw new Error(result.data?.message || "Failed to delete entry");
    window.notify(result.data?.message || "Deleted", "success");
    loadCompanyRoadmaps(currentPage);
}

document.addEventListener("DOMContentLoaded", () => {
    const perPageSelect = document.getElementById("perPageSelect");
    const searchInput = document.getElementById("searchInput");
    const orderSelect = document.getElementById("orderSelect");
    const employmentTypeFilterSelect = document.getElementById("employmentTypeFilterSelect");
    const activeFilterSelect = document.getElementById("activeFilterSelect");

    perPageSelect?.addEventListener("change", () => {
        perPage = Number(perPageSelect.value || 10);
        currentPage = 1;
        loadCompanyRoadmaps(currentPage);
    });

    searchInput?.addEventListener("input", (event) => {
        const nextValue = String(event.target.value || "").trim();
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            searchQuery = nextValue;
            currentPage = 1;
            loadCompanyRoadmaps(currentPage);
        }, 300);
    });

    orderSelect?.addEventListener("change", (event) => {
        sortOrder = String(event.target.value || "asc");
        currentPage = 1;
        loadCompanyRoadmaps(currentPage);
    });

    employmentTypeFilterSelect?.addEventListener("change", (event) => {
        employmentTypeFilter = String(event.target.value || "").trim();
        currentPage = 1;
        loadCompanyRoadmaps(currentPage);
    });

    activeFilterSelect?.addEventListener("change", (event) => {
        activeFilter = String(event.target.value || "").trim();
        currentPage = 1;
        loadCompanyRoadmaps(currentPage);
    });

    document.getElementById("prevPage")?.addEventListener("click", () => {
        if (currentPage <= 1) return;
        currentPage -= 1;
        loadCompanyRoadmaps(currentPage);
    });

    document.getElementById("nextPage")?.addEventListener("click", () => {
        currentPage += 1;
        loadCompanyRoadmaps(currentPage);
    });

    document.addEventListener("click", (event) => {
        const addBtn = event.target.closest("[data-add-activity-row]");
        if (addBtn) {
            const targetSelector = addBtn.getAttribute("data-target");
            if (targetSelector) appendActivityRow(targetSelector);
            return;
        }

        const removeBtn = event.target.closest("[data-remove-activity-row]");
        if (removeBtn) {
            removeBtn.closest("[data-activity-row]")?.remove();
        }
    });

    document.getElementById("addRoadmapModal")?.addEventListener("show.bs.modal", () => {
        document.getElementById("addCompanyRoadmapForm")?.reset();
        const rows = document.getElementById("addActivityRows");
        if (rows) rows.innerHTML = "";
        const color = document.getElementById("addAccentColor");
        if (color) color.value = "#2962ff";
        const active = document.getElementById("addIsActive");
        if (active) active.checked = true;
    });

    loadCompanyRoadmaps(currentPage);
});

window.addCompanyRoadmap = addCompanyRoadmap;
window.updateCompanyRoadmap = updateCompanyRoadmap;
window.deleteCompanyRoadmap = deleteCompanyRoadmap;
window.playCompanyRoadmapPreview = playCompanyRoadmapPreview;

