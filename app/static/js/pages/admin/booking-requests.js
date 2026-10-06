import { AdminBookingRequestsService } from "../../services/AdminBookingRequestsService.js";

const service = new AdminBookingRequestsService();

let currentPage = 1;
let perPage = 10;
let searchQuery = "";
let sortOrder = "desc";
let searchDebounceTimer = null;

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function hideDeleteConfirmModal() {
    const modalEl = document.getElementById("deleteConfirmModal");
    if (modalEl && window.bootstrap && window.bootstrap.Modal) {
        const instance = window.bootstrap.Modal.getInstance(modalEl);
        if (instance) instance.hide();
    }
}

async function loadBookingRequests(page = 1) {
    const tbody = document.getElementById("bookingRequestsTableBody");
    const pageInfo = document.getElementById("pageInfo");

    tbody.innerHTML = `<tr><td colspan="8" class="text-center">Loading...</td></tr>`;

    try {
        const data = await service.fetchList({
            page,
            perPage,
            order: sortOrder,
            search: searchQuery,
        });

        tbody.innerHTML = "";

        const clearBtn = document.getElementById("clearBookingRequestsBtn");
        if (!data.booking_requests || data.booking_requests.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center">No booking requests found</td></tr>`;
            pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
            if (clearBtn) clearBtn.disabled = true;
            return;
        }
        if (clearBtn) clearBtn.disabled = false;

        data.booking_requests.forEach((req, index) => {
            const fullMsg = escapeHtml(req.message || "");
            const maxMsgLen = 50;
            const isLong = fullMsg.length > maxMsgLen;

            let msgHtml;
            if (isLong) {
                msgHtml = `<span class="msg-text" data-expanded="false">${fullMsg.slice(0, maxMsgLen)}...</span>
                    <a href="#" class="msg-toggle text-primary small">Show more</a>`;
            } else {
                msgHtml = `<span class="msg-text">${fullMsg}</span>`;
            }

            tbody.innerHTML += `
            <tr>
                <td>${(page - 1) * perPage + (index + 1)}</td>
                <td>${escapeHtml(req.name)}</td>
                <td>${escapeHtml(req.email)}</td>
                <td>${escapeHtml(req.preferred_date)}</td>
                <td>${escapeHtml(req.preferred_time)}</td>
                <td style="max-width:200px">${msgHtml}</td>
                <td>${escapeHtml(req.created_at || "")}</td>
                <td>
                    <button class="btn btn-sm btn-danger booking-delete-btn"
                        data-record-id="${escapeHtml(req._id)}">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </td>
            </tr>`;
        });

        tbody.querySelectorAll(".msg-toggle").forEach(function (el) {
            el.addEventListener("click", function (e) {
                e.preventDefault();
                const td = this.closest("td");
                const span = td.querySelector(".msg-text");
                const isExpanded = span.dataset.expanded === "true";
                span.textContent = isExpanded ? fullMsgForToggle(td) : fullMsgForToggle(td);
                span.dataset.expanded = isExpanded ? "false" : "true";
                this.textContent = isExpanded ? "Show more" : "Show less";

                function fullMsgForToggle(td) {
                    const reqId = td.closest("tr").querySelector(".booking-delete-btn").dataset.recordId;
                    const req = data.booking_requests.find(function (r) { return r._id === reqId; });
                    return req ? escapeHtml(req.message || "") : "";
                }

                if (!isExpanded) {
                    span.textContent = fullMsgForToggle(td);
                }
            });
        });

        tbody.querySelectorAll(".booking-delete-btn").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const recordId = this.dataset.recordId;
                window.confirmDelete(
                    "Are you sure you want to delete this booking request?",
                    async function () {
                        const result = await service.remove(recordId);
                        if (result.ok) {
                            hideDeleteConfirmModal();
                            window.notify(result.data?.message || "Deleted.", "success");
                            loadBookingRequests(currentPage);
                        } else {
                            window.notify("Failed to delete booking request.", "error");
                        }
                    }
                );
            });
        });

        pageInfo.textContent = `Page ${page} | ${data.total_pages}`;
        document.getElementById("prevPage").disabled = page <= 1;
        document.getElementById("nextPage").disabled = page == data.total_pages;
    } catch (error) {
        console.error("Error fetching booking requests:", error);
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error loading data</td></tr>`;
    }
}

document.addEventListener("DOMContentLoaded", function () {
    loadBookingRequests(currentPage);

    document.getElementById("prevPage").addEventListener("click", function () {
        if (currentPage > 1) {
            currentPage--;
            loadBookingRequests(currentPage);
        }
    });

    document.getElementById("nextPage").addEventListener("click", function () {
        currentPage++;
        loadBookingRequests(currentPage);
    });

    document.getElementById("perPageSelect").addEventListener("change", function (e) {
        perPage = parseInt(e.target.value);
        currentPage = 1;
        loadBookingRequests(currentPage);
    });

    const searchInput = document.getElementById("searchInput");
    const orderSelect = document.getElementById("orderSelect");

    searchInput?.addEventListener("input", function (event) {
        const nextValue = String(event.target.value || "").trim();
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(function () {
            searchQuery = nextValue;
            currentPage = 1;
            loadBookingRequests(currentPage);
        }, 300);
    });

    orderSelect?.addEventListener("change", function (event) {
        sortOrder = String(event.target.value || "desc");
        currentPage = 1;
        loadBookingRequests(currentPage);
    });

    document.getElementById("clearBookingRequestsBtn")?.addEventListener("click", function () {
        window.confirmDelete(
            "Are you sure you want to delete all booking requests?",
            async function () {
                const result = await service.clearAll();
                if (result.ok) {
                    hideDeleteConfirmModal();
                    window.notify(result.data?.message || "All booking requests cleared.", "success");
                    currentPage = 1;
                    loadBookingRequests(currentPage);
                } else {
                    window.notify("Failed to clear booking requests.", "error");
                }
            }
        );
    });
});
