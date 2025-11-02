let currentPage = 1;
let currentAudio = null;
let currentButton = null;
let perPage = 10;
let currentIP = null;

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

async function getCurrentIP() {
    try {
        const res = await fetch("/admin/api/get-client-ip");
        const data = await res.json();
        currentIP = data.ip;
        console.log("Current Device IP:", currentIP);
    } catch (error) {
        console.error("Failed to get local IP from backend:", error);
    }
}

async function loadLoginAttempt(page = 1) {
    const tbody = document.getElementById("loginAttemptsTableBody");
    const modalContainer = document.getElementById("loginAttemptsModals");
    const pageInfo = document.getElementById("pageInfo");

    // ✅ Show loading row
    tbody.innerHTML = `<tr><td colspan="6" class="text-center">Loading...</td></tr>`;
    modalContainer.innerHTML = "";

    try {
        const response = await fetch(
            `/admin/api/login-attempts?page=${page}&per_page=${perPage}&order=desc`
        );
        const data = await response.json();

        tbody.innerHTML = ""; // clear loading
        modalContainer.innerHTML = "";

        if (!data.login_attempt || data.login_attempt.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center">No login attempt found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
            return;
        }

        data.login_attempt.forEach((loginAttempt, index) => {
            const modalIdDelete = `deleteModal${page}_${index}`;
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
                    <button ${isCurrent ? 'disabled' : ''} class="btn btn-sm btn-${isCurrent ? 'secondary' : 'danger'}" data-bs-toggle="modal" data-bs-target="#${modalIdDelete}">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </td>
            </tr>
            `;

            // ✅ Add Delete modal
            modalContainer.innerHTML += `
            <div class="modal fade" id="${modalIdDelete}" tabindex="-1" aria-labelledby="${modalIdDelete}Label" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="${modalIdDelete}Label">Delete Login Attempt</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    Are you sure you want to delete login attempts from <strong>${loginAttempt._id}</strong>?
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-danger" onclick="deleteLoginAttempt('${loginAttempt._id}', '${modalIdDelete}')">Delete</button>
                </div>
                </div>
            </div>
            </div>
            `;
        });

        // ✅ Update page info
        pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
        document.getElementById("prevPage").disabled = page <= 1;
        document.getElementById("nextPage").disabled = page == data.total_pages;
    } catch (error) {
        console.error("Error fetching login attempt list:", error);
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error loading data</td></tr>`;
    }
}

async function deleteLoginAttempt(loginAttemptId, modalId) {
    const res = await fetch(`/admin/api/delete-login-attempt/${loginAttemptId}`, {
        method: "DELETE",
    });

    if (res.ok) {
        bootstrap.Modal.getInstance(document.getElementById(modalId)).hide();
        const data = await res.json();
        loadLoginAttempt(currentPage);
        alert(data.message);
    } else {
        alert("Failed to delete login attempt.");
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
        currentPage = 1; // reset to first page when perPage changes
        loadLoginAttempt(currentPage);
    });
});