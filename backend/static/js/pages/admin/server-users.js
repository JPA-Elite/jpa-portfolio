import { AdminCrudService } from "../../services/AdminCrudService.js";

const serverUserService = new AdminCrudService("server-user");

let currentPage = 1;
let perPage = 10;
let searchQuery = "";
let sortOrder = "desc";
let accountTypeFilter = "";
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

function accountTypeBadge(value) {
    return value === "admin"
        ? `<span class="badge text-bg-danger">Admin</span>`
        : `<span class="badge text-bg-primary">Member</span>`;
}

async function loadServerUsers(page = 1) {
    const tbody = document.getElementById("serverUsersTableBody");
    const modalContainer = document.getElementById("serverUserModals");
    const pageInfo = document.getElementById("pageInfo");

    tbody.innerHTML = `<tr><td colspan="10" class="text-center">Loading...</td></tr>`;
    modalContainer.innerHTML = "";

    try {
        const data = await serverUserService.fetchList({
            page,
            perPage,
            order: sortOrder,
            search: searchQuery,
            account_type: accountTypeFilter,
        });

        const rows = data.users || [];
        tbody.innerHTML = "";

        if (!rows.length) {
            tbody.innerHTML = `<tr><td colspan="10" class="text-center">No server users found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages || 1}`;
            document.getElementById("prevPage").disabled = true;
            document.getElementById("nextPage").disabled = true;
            return;
        }

        rows.forEach((user, index) => {
            const rowNo = (page - 1) * perPage + index + 1;
            const editModalId = `editServerUserModal_${page}_${index}`;
            const deleteModalId = `deleteServerUserModal_${page}_${index}`;

            tbody.insertAdjacentHTML("beforeend", `
                <tr>
                    <td>${rowNo}</td>
                    <td>${escapeHtml(user.name || "")}</td>
                    <td>${escapeHtml(user.username || "")}</td>
                    <td>${escapeHtml(user.email || "")}</td>
                    <td>${accountTypeBadge(user.account_type || "member")}</td>
                    <td>${escapeHtml(user.birthdate || "-")}</td>
                    <td>${escapeHtml(user.place || "-")}</td>
                    <td>${escapeHtml(user.gender || "-")}</td>
                    <td>${user.is_active === false ? '<span class="badge text-bg-secondary">No</span>' : '<span class="badge text-bg-success">Yes</span>'}</td>
                    <td>
                      <div class="d-flex flex-wrap gap-1">
                        <button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#${editModalId}">
                          <i class="bi bi-pencil"></i> Edit
                        </button>
                        <button class="btn btn-sm btn-danger" data-bs-toggle="modal" data-bs-target="#${deleteModalId}">
                          <i class="bi bi-trash"></i> Delete
                        </button>
                      </div>
                    </td>
                </tr>
            `);

            modalContainer.insertAdjacentHTML("beforeend", buildEditModal(user, editModalId, page, index));
            modalContainer.insertAdjacentHTML("beforeend", buildDeleteModal(user, deleteModalId));
        });

        pageInfo.textContent = `Page ${page} | ${data.total_pages || 1}`;
        document.getElementById("prevPage").disabled = page <= 1;
        document.getElementById("nextPage").disabled = page >= (data.total_pages || 1);
    } catch (error) {
        console.error(error);
        tbody.innerHTML = `<tr><td colspan="10" class="text-center text-danger">Error loading server users</td></tr>`;
    }
}

function buildEditModal(user, modalId, page, index) {
    const suffix = `_${page}_${index}`;
    return `
    <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Server User</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <form id="editServerUserForm${suffix}">
              <div class="row g-3">
                <div class="col-md-6"><label class="form-label">Name</label><input id="editName${suffix}" class="form-control" value="${escapeHtml(user.name || "")}"></div>
                <div class="col-md-6"><label class="form-label">Birthdate</label><input id="editBirthdate${suffix}" type="date" class="form-control" value="${escapeHtml(user.birthdate || "")}"></div>
                <div class="col-md-6"><label class="form-label">Place</label><input id="editPlace${suffix}" class="form-control" value="${escapeHtml(user.place || "")}"></div>
                <div class="col-md-6"><label class="form-label">Gender</label><input id="editGender${suffix}" class="form-control" value="${escapeHtml(user.gender || "")}"></div>
                <div class="col-md-6"><label class="form-label">Username</label><input id="editUsername${suffix}" class="form-control" value="${escapeHtml(user.username || "")}"></div>
                <div class="col-md-6"><label class="form-label">Email</label><input id="editEmail${suffix}" type="email" class="form-control" value="${escapeHtml(user.email || "")}"></div>
                <div class="col-md-6"><label class="form-label">New Password (optional)</label><input id="editPassword${suffix}" type="password" class="form-control"></div>
                <div class="col-md-6">
                  <label class="form-label">Account Type</label>
                  <select id="editAccountType${suffix}" class="form-select">
                    <option value="member" ${user.account_type === "member" ? "selected" : ""}>Member</option>
                    <option value="admin" ${user.account_type === "admin" ? "selected" : ""}>Admin</option>
                  </select>
                </div>
                <div class="col-12 form-check ms-2">
                  <input class="form-check-input" id="editIsActive${suffix}" type="checkbox" ${user.is_active === false ? "" : "checked"}>
                  <label class="form-check-label" for="editIsActive${suffix}">Active account</label>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-primary" id="editServerUserBtn_${user.id}"
              data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Saving...'
              onclick="updateServerUser('${user.id}', '${suffix}')">Save changes</button>
          </div>
        </div>
      </div>
    </div>`;
}

function buildDeleteModal(user, modalId) {
    return `
    <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Delete Server User</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            Are you sure you want to delete <strong>${escapeHtml(user.username || "this user")}</strong>?
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-danger" id="deleteServerUserBtn_${user.id}"
              data-loading-text='<span class="spinner-border spinner-border-sm me-2"></span> Deleting...'
              onclick="deleteServerUser('${user.id}', '${modalId}')">Delete</button>
          </div>
        </div>
      </div>
    </div>`;
}

function formDataFromAddForm() {
    const data = new FormData();
    data.append("name", document.getElementById("addName").value.trim());
    data.append("birthdate", document.getElementById("addBirthdate").value);
    data.append("place", document.getElementById("addPlace").value.trim());
    data.append("gender", document.getElementById("addGender").value.trim());
    data.append("username", document.getElementById("addUsername").value.trim());
    data.append("email", document.getElementById("addEmail").value.trim());
    data.append("password", document.getElementById("addPassword").value);
    data.append("account_type", document.getElementById("addAccountType").value);
    return data;
}

async function addServerUser() {
    const button = document.getElementById("addServerUserBtn");
    setButtonLoading(button, true);
    try {
        const result = await serverUserService.add(formDataFromAddForm());
        if (!result.ok) throw new Error(result.data?.message || "Failed to add server user");

        window.notify?.(result.data?.message || "Server user added", "success");
        bootstrap.Modal.getInstance(document.getElementById("addServerUserModal"))?.hide();
        document.getElementById("addServerUserForm").reset();
        loadServerUsers(currentPage);
    } catch (error) {
        console.error(error);
        window.notify?.(error.message || "Failed to add server user", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

async function updateServerUser(userId, suffix) {
    const button = document.getElementById(`editServerUserBtn_${userId}`);
    setButtonLoading(button, true);

    try {
        const data = new FormData();
        data.append("name", document.getElementById(`editName${suffix}`).value.trim());
        data.append("birthdate", document.getElementById(`editBirthdate${suffix}`).value);
        data.append("place", document.getElementById(`editPlace${suffix}`).value.trim());
        data.append("gender", document.getElementById(`editGender${suffix}`).value.trim());
        data.append("username", document.getElementById(`editUsername${suffix}`).value.trim());
        data.append("email", document.getElementById(`editEmail${suffix}`).value.trim());
        data.append("password", document.getElementById(`editPassword${suffix}`).value);
        data.append("account_type", document.getElementById(`editAccountType${suffix}`).value);
        data.append("is_active", document.getElementById(`editIsActive${suffix}`).checked ? "true" : "false");

        const result = await serverUserService.update(userId, data);
        if (!result.ok) throw new Error(result.data?.message || "Failed to update server user");

        window.notify?.(result.data?.message || "Server user updated", "success");
        bootstrap.Modal.getInstance(button.closest(".modal"))?.hide();
        loadServerUsers(currentPage);
    } catch (error) {
        console.error(error);
        window.notify?.(error.message || "Failed to update server user", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

async function deleteServerUser(userId, modalId) {
    const button = document.getElementById(`deleteServerUserBtn_${userId}`);
    setButtonLoading(button, true);
    try {
        const result = await serverUserService.remove(userId);
        if (!result.ok) throw new Error(result.data?.message || "Failed to delete server user");

        window.notify?.(result.data?.message || "Server user deleted", "success");
        bootstrap.Modal.getInstance(document.getElementById(modalId))?.hide();
        loadServerUsers(currentPage);
    } catch (error) {
        console.error(error);
        window.notify?.(error.message || "Failed to delete server user", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const perPageSelect = document.getElementById("perPageSelect");
    const searchInput = document.getElementById("searchInput");
    const orderSelect = document.getElementById("orderSelect");
    const accountTypeFilterSelect = document.getElementById("accountTypeFilterSelect");

    perPageSelect?.addEventListener("change", () => {
        perPage = Number(perPageSelect.value || 10);
        currentPage = 1;
        loadServerUsers(currentPage);
    });

    searchInput?.addEventListener("input", (event) => {
        const nextValue = String(event.target.value || "").trim();
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            searchQuery = nextValue;
            currentPage = 1;
            loadServerUsers(currentPage);
        }, 300);
    });

    orderSelect?.addEventListener("change", (event) => {
        sortOrder = String(event.target.value || "desc");
        currentPage = 1;
        loadServerUsers(currentPage);
    });

    accountTypeFilterSelect?.addEventListener("change", (event) => {
        accountTypeFilter = String(event.target.value || "").trim();
        currentPage = 1;
        loadServerUsers(currentPage);
    });

    document.getElementById("prevPage")?.addEventListener("click", () => {
        if (currentPage <= 1) return;
        currentPage -= 1;
        loadServerUsers(currentPage);
    });

    document.getElementById("nextPage")?.addEventListener("click", () => {
        currentPage += 1;
        loadServerUsers(currentPage);
    });

    loadServerUsers(currentPage);
});

window.addServerUser = addServerUser;
window.updateServerUser = updateServerUser;
window.deleteServerUser = deleteServerUser;
