import { AdminCrudService } from "../../services/AdminCrudService.js";

const serverChannelService = new AdminCrudService("server-channel");

let currentPage = 1;
let perPage = 10;
let searchQuery = "";
let sortOrder = "desc";
let channelTypeFilter = "";
let visibilityFilter = "";
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

async function loadServerChannels(page = 1) {
    const tbody = document.getElementById("serverChannelsTableBody");
    const modalContainer = document.getElementById("serverChannelModals");
    const pageInfo = document.getElementById("pageInfo");

    tbody.innerHTML = `<tr><td colspan="8" class="text-center">Loading...</td></tr>`;
    modalContainer.innerHTML = "";

    try {
        const data = await serverChannelService.fetchList({
            page,
            perPage,
            order: sortOrder,
            search: searchQuery,
            channel_type: channelTypeFilter,
            visibility: visibilityFilter,
        });
        const rows = data.channels || [];

        tbody.innerHTML = "";
        if (!rows.length) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center">No channels found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages || 1}`;
            document.getElementById("prevPage").disabled = true;
            document.getElementById("nextPage").disabled = true;
            return;
        }

        rows.forEach((channel, index) => {
            const rowNo = (page - 1) * perPage + index + 1;
            const editModalId = `editServerChannelModal_${page}_${index}`;
            const deleteModalId = `deleteServerChannelModal_${page}_${index}`;
            const isDefault = ["general", "business-concerns"].includes(channel.slug);

            tbody.insertAdjacentHTML("beforeend", `
                <tr>
                  <td>${rowNo}</td>
                  <td>${escapeHtml(channel.name || "")}</td>
                  <td>${escapeHtml(channel.slug || "")}</td>
                  <td><span class="badge text-bg-info">${escapeHtml(channel.channel_type || "custom")}</span></td>
                  <td>${channel.is_public ? '<span class="badge text-bg-success">Public</span>' : '<span class="badge text-bg-secondary">Private</span>'}</td>
                  <td>${Array.isArray(channel.member_ids) ? channel.member_ids.length : 0}</td>
                  <td>${escapeHtml(channel.description || "-")}</td>
                  <td>
                    <div class="d-flex flex-wrap gap-1">
                      <button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#${editModalId}">
                        <i class="bi bi-pencil"></i> Edit
                      </button>
                      <button class="btn btn-sm btn-danger" ${isDefault ? "disabled" : ""} data-bs-toggle="modal" data-bs-target="#${deleteModalId}">
                        <i class="bi bi-trash"></i> Delete
                      </button>
                    </div>
                  </td>
                </tr>
            `);

            modalContainer.insertAdjacentHTML("beforeend", buildEditModal(channel, editModalId, page, index));
            modalContainer.insertAdjacentHTML("beforeend", buildDeleteModal(channel, deleteModalId, isDefault));
        });

        pageInfo.textContent = `Page ${page} | ${data.total_pages || 1}`;
        document.getElementById("prevPage").disabled = page <= 1;
        document.getElementById("nextPage").disabled = page >= (data.total_pages || 1);
    } catch (error) {
        console.error(error);
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error loading channels</td></tr>`;
    }
}

function buildEditModal(channel, modalId, page, index) {
    const suffix = `_${page}_${index}`;
    return `
    <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Channel</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <form id="editServerChannelForm${suffix}">
              <div class="mb-3">
                <label class="form-label">Name</label>
                <input id="editName${suffix}" class="form-control" value="${escapeHtml(channel.name || "")}">
              </div>
              <div class="mb-3">
                <label class="form-label">Description</label>
                <textarea id="editDescription${suffix}" class="form-control" rows="2">${escapeHtml(channel.description || "")}</textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">Type</label>
                <select id="editType${suffix}" class="form-select">
                  <option value="custom" ${channel.channel_type === "custom" ? "selected" : ""}>Custom</option>
                  <option value="business" ${channel.channel_type === "business" ? "selected" : ""}>Business</option>
                  <option value="general" ${channel.channel_type === "general" ? "selected" : ""}>General</option>
                  <option value="concern" ${channel.channel_type === "concern" ? "selected" : ""}>Concern</option>
                </select>
              </div>
              <div class="form-check">
                <input id="editIsPublic${suffix}" class="form-check-input" type="checkbox" ${channel.is_public ? "checked" : ""}>
                <label class="form-check-label" for="editIsPublic${suffix}">Public channel</label>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-primary" id="editServerChannelBtn_${channel.id}"
              data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Saving...'
              onclick="updateServerChannel('${channel.id}', '${suffix}')">Save changes</button>
          </div>
        </div>
      </div>
    </div>`;
}

function buildDeleteModal(channel, modalId, isDefault) {
    return `
    <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Delete Channel</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            ${isDefault
                ? `<div class="text-warning">Default channels cannot be deleted.</div>`
                : `Are you sure you want to delete <strong>${escapeHtml(channel.name || "this channel")}</strong>?`}
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-danger" id="deleteServerChannelBtn_${channel.id}"
              ${isDefault ? "disabled" : ""}
              data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Deleting...'
              onclick="deleteServerChannel('${channel.id}', '${modalId}')">Delete</button>
          </div>
        </div>
      </div>
    </div>`;
}

async function addServerChannel() {
    const button = document.getElementById("addServerChannelBtn");
    setButtonLoading(button, true);
    try {
        const data = new FormData();
        data.append("name", document.getElementById("addName").value.trim());
        data.append("description", document.getElementById("addDescription").value.trim());
        data.append("channel_type", document.getElementById("addType").value);
        data.append("is_public", document.getElementById("addIsPublic").checked ? "true" : "false");

        const result = await serverChannelService.add(data);
        if (!result.ok) throw new Error(result.data?.message || "Failed to add channel");

        window.notify?.(result.data?.message || "Channel added", "success");
        bootstrap.Modal.getInstance(document.getElementById("addServerChannelModal"))?.hide();
        document.getElementById("addServerChannelForm").reset();
        document.getElementById("addIsPublic").checked = true;
        loadServerChannels(currentPage);
    } catch (error) {
        console.error(error);
        window.notify?.(error.message || "Failed to add channel", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

async function updateServerChannel(channelId, suffix) {
    const button = document.getElementById(`editServerChannelBtn_${channelId}`);
    setButtonLoading(button, true);
    try {
        const data = new FormData();
        data.append("name", document.getElementById(`editName${suffix}`).value.trim());
        data.append("description", document.getElementById(`editDescription${suffix}`).value.trim());
        data.append("channel_type", document.getElementById(`editType${suffix}`).value);
        data.append("is_public", document.getElementById(`editIsPublic${suffix}`).checked ? "true" : "false");

        const result = await serverChannelService.update(channelId, data);
        if (!result.ok) throw new Error(result.data?.message || "Failed to update channel");

        window.notify?.(result.data?.message || "Channel updated", "success");
        bootstrap.Modal.getInstance(button.closest(".modal"))?.hide();
        loadServerChannels(currentPage);
    } catch (error) {
        console.error(error);
        window.notify?.(error.message || "Failed to update channel", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

async function deleteServerChannel(channelId, modalId) {
    const button = document.getElementById(`deleteServerChannelBtn_${channelId}`);
    setButtonLoading(button, true);
    try {
        const result = await serverChannelService.remove(channelId);
        if (!result.ok) throw new Error(result.data?.message || "Failed to delete channel");

        window.notify?.(result.data?.message || "Channel deleted", "success");
        bootstrap.Modal.getInstance(document.getElementById(modalId))?.hide();
        loadServerChannels(currentPage);
    } catch (error) {
        console.error(error);
        window.notify?.(error.message || "Failed to delete channel", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const perPageSelect = document.getElementById("perPageSelect");
    const searchInput = document.getElementById("searchInput");
    const orderSelect = document.getElementById("orderSelect");
    const channelTypeFilterSelect = document.getElementById("channelTypeFilterSelect");
    const visibilityFilterSelect = document.getElementById("visibilityFilterSelect");

    perPageSelect?.addEventListener("change", () => {
        perPage = Number(perPageSelect.value || 10);
        currentPage = 1;
        loadServerChannels(currentPage);
    });

    searchInput?.addEventListener("input", (event) => {
        const nextValue = String(event.target.value || "").trim();
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            searchQuery = nextValue;
            currentPage = 1;
            loadServerChannels(currentPage);
        }, 300);
    });

    orderSelect?.addEventListener("change", (event) => {
        sortOrder = String(event.target.value || "desc");
        currentPage = 1;
        loadServerChannels(currentPage);
    });

    channelTypeFilterSelect?.addEventListener("change", (event) => {
        channelTypeFilter = String(event.target.value || "").trim();
        currentPage = 1;
        loadServerChannels(currentPage);
    });

    visibilityFilterSelect?.addEventListener("change", (event) => {
        visibilityFilter = String(event.target.value || "").trim();
        currentPage = 1;
        loadServerChannels(currentPage);
    });

    document.getElementById("prevPage")?.addEventListener("click", () => {
        if (currentPage <= 1) return;
        currentPage -= 1;
        loadServerChannels(currentPage);
    });

    document.getElementById("nextPage")?.addEventListener("click", () => {
        currentPage += 1;
        loadServerChannels(currentPage);
    });

    loadServerChannels(currentPage);
});

window.addServerChannel = addServerChannel;
window.updateServerChannel = updateServerChannel;
window.deleteServerChannel = deleteServerChannel;
