import { AdminLoginAttemptsService } from "../../services/AdminLoginAttemptsService.js";

const loginAttemptsService = new AdminLoginAttemptsService();

let currentPage = 1;
let perPage = 10;
let currentIP = null;
let searchQuery = "";
let sortOrder = "desc";
let searchDebounceTimer = null;

async function getCurrentIP() {
    try {
        const data = await loginAttemptsService.fetchClientIp();
        currentIP = data.ip;
        console.log("Current Device IP:", currentIP);
    } catch (error) {
        console.error("Failed to get local IP from app:", error);
    }
}

async function loadLoginAttempt(page = 1) {
    const tbody = document.getElementById("loginAttemptsTableBody");
    const pageInfo = document.getElementById("pageInfo");

    tbody.innerHTML = `<tr><td colspan="6" class="text-center">Loading...</td></tr>`;

    try {
        const data = await loginAttemptsService.fetchList({
            page,
            perPage,
            order: sortOrder,
            search: searchQuery,
        });

        tbody.innerHTML = "";

        if (!data.login_attempt || data.login_attempt.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center">No login attempt found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
            return;
        }

        data.login_attempt.forEach((loginAttempt, index) => {
            const ipList = currentIP ? currentIP.split(",").map(ip => ip.trim()) : [];
            const isCurrent = ipList.includes(loginAttempt._id);

            tbody.innerHTML += `
            <tr ${isCurrent ? 'class="table-success"' : ""}>
                <td>${(page - 1) * perPage + (index + 1)}</td>
                <td>
                    ${loginAttempt._id}
                    ${isCurrent ? '<span class="badge bg-success ms-2">(Current Device)</span>' : ''}
                </td>
                <td>${loginAttempt.attempts}</td>
                <td>${loginAttempt.lockout_until}</td>
                <td>
                    <button ${isCurrent ? 'disabled' : ''} class="btn btn-sm btn-${isCurrent ? 'secondary' : 'danger'} login-attempt-delete-btn"
                        data-record-id="${loginAttempt._id}">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </td>
            </tr>
            `;
        });

        // Attach delete handlers
        tbody.querySelectorAll(".login-attempt-delete-btn").forEach((btn) => {
            btn.addEventListener("click", function () {
                const recordId = this.dataset.recordId;
                window.confirmDelete(
                    `Are you sure you want to delete login attempts from <strong>${recordId}</strong>?`,
                    async () => {
                        const result = await loginAttemptsService.remove(recordId);
                        if (result.ok) {
                            bootstrap.Modal.getInstance(document.getElementById("deleteConfirmModal")).hide();
                            window.notify(result.data?.message || "Deleted.", "success");
                            loadLoginAttempt(currentPage);
                        } else {
                            window.notify("Failed to delete login attempt.", "error");
                        }
                    }
                );
            });
        });

        pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
        document.getElementById("prevPage").disabled = page <= 1;
        document.getElementById("nextPage").disabled = page == data.total_pages;
    } catch (error) {
        console.error("Error fetching login attempt list:", error);
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error loading data</td></tr>`;
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    await getCurrentIP();
    loadLoginAttempt(currentPage);

    document.getElementById("prevPage").addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            loadLoginAttempt(currentPage);
        }
    });

    document.getElementById("nextPage").addEventListener("click", () => {
        currentPage++;
        loadLoginAttempt(currentPage);
    });

    document.getElementById("perPageSelect").addEventListener("change", (e) => {
        perPage = parseInt(e.target.value);
        currentPage = 1;
        loadLoginAttempt(currentPage);
    });

    const searchInput = document.getElementById("searchInput");
    const orderSelect = document.getElementById("orderSelect");

    searchInput?.addEventListener("input", (event) => {
        const nextValue = String(event.target.value || "").trim();
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            searchQuery = nextValue;
            currentPage = 1;
            loadLoginAttempt(currentPage);
        }, 300);
    });

    orderSelect?.addEventListener("change", (event) => {
        sortOrder = String(event.target.value || "desc");
        currentPage = 1;
        loadLoginAttempt(currentPage);
    });
});