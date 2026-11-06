// pages/dashboard.js
import { AdminDashboardService } from "../../services/AdminDashboardService.js";

// Count animation utility
function animateCount(element, start, end, duration) {
    if (!element) return;
    if (start === end) {
        element.textContent = end.toLocaleString();
        return;
    }
    const range = end - start;
    let current = start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.max(12, Math.abs(Math.floor(duration / range)));
    const timer = setInterval(() => {
        current += increment;
        element.textContent = current.toLocaleString();
        if (current === end) clearInterval(timer);
    }, stepTime);
}

function formatTimestamp(date = new Date(), timeZone) {
    const options = {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    };
    if (timeZone) options.timeZone = timeZone;
    return date.toLocaleString(undefined, options);
}

function formatVisitTimestamp(item) {
    if (item.occurred_at) {
        const occurred = new Date(item.occurred_at);
        if (!isNaN(occurred.getTime())) return formatTimestamp(occurred, "Asia/Manila");
    }
    return item.timestamp || "-";
}

const SOCIAL_PAGE_PATHS = new Set(["/vlog", "/music", "/concern", "/donation", "/visitors"]);
const KNOWN_SITES = new Set(["professional", "social", "admin"]);

function formatSiteLabel(item) {
    const site = String(item?.site || "").trim().toLowerCase();
    if (KNOWN_SITES.has(site)) return site.charAt(0).toUpperCase() + site.slice(1);
    const page = String(item?.page || "").trim().replace(/\/+$/, "") || "/";
    if (page === "/admin" || page.startsWith("/admin/")) return "Admin";
    if (SOCIAL_PAGE_PATHS.has(page)) return "Social";
    return "Professional";
}

const DEVICE_CHART_COLORS = ["#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#64748b"];
const DEVICE_CHART_RADIUS = 82;
const DEVICE_CHART_CIRCUMFERENCE = 2 * Math.PI * DEVICE_CHART_RADIUS;

function escapeHtml(value = "") {
    return String(value).replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }[character]));
}

function formatSharePercentage(share) {
    const percentage = share * 100;
    if (percentage > 0 && percentage < 10) return `${percentage.toFixed(1)}%`;
    return `${Math.round(percentage)}%`;
}

function renderDeviceBreakdown(items) {
    const segmentsGroup = document.getElementById("deviceDonutSegments");
    const legend = document.getElementById("deviceBreakdownLegend");
    const totalCount = document.getElementById("deviceBreakdownTotalCount");
    const totalBadge = document.getElementById("deviceBreakdownTotal");
    const emptyState = document.getElementById("deviceBreakdownEmpty");
    const chart = document.getElementById("deviceBreakdownChart");

    if (!segmentsGroup || !legend || !totalCount) return;

    const rows = (Array.isArray(items) ? items : [])
        .map((item) => ({
            label: String(item?.label || "Other"),
            count: Math.max(0, Number(item?.count || 0)),
        }))
        .filter((item) => item.count > 0);

    const total = rows.reduce((sum, item) => sum + item.count, 0);
    segmentsGroup.innerHTML = "";
    legend.innerHTML = "";

    if (!rows.length || total === 0) {
        totalCount.textContent = "0";
        if (totalBadge) totalBadge.textContent = "0 visits";
        if (emptyState) emptyState.hidden = false;
        if (chart) chart.classList.add("is-empty");
        return;
    }

    if (emptyState) emptyState.hidden = true;
    if (chart) chart.classList.remove("is-empty");
    totalCount.textContent = total.toLocaleString();
    if (totalBadge) totalBadge.textContent = `${total.toLocaleString()} ${total === 1 ? "visit" : "visits"}`;

    const gap = rows.length > 1 ? Math.min(4, DEVICE_CHART_CIRCUMFERENCE * 0.008) : 0;
    const segmentElements = [];
    const legendElements = [];
    let offset = 0;

    rows.forEach((item, index) => {
        const color = DEVICE_CHART_COLORS[index % DEVICE_CHART_COLORS.length];
        const share = item.count / total;
        const arcLength = Math.max(share * DEVICE_CHART_CIRCUMFERENCE - gap, 0.6);

        const segment = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        segment.setAttribute("cx", "110");
        segment.setAttribute("cy", "110");
        segment.setAttribute("r", String(DEVICE_CHART_RADIUS));
        segment.setAttribute("transform", "rotate(-90 110 110)");
        segment.setAttribute("stroke", color);
        segment.setAttribute("stroke-dasharray", `0 ${DEVICE_CHART_CIRCUMFERENCE}`);
        segment.setAttribute("stroke-dashoffset", String(-offset));
        segment.setAttribute("tabindex", "0");
        segment.setAttribute("role", "img");
        segment.setAttribute(
            "aria-label",
            `${item.label}: ${formatSharePercentage(share)} (${item.count} visits)`
        );
        segment.classList.add("visitor-devices-segment");
        segment.dataset.index = String(index);
        segmentsGroup.appendChild(segment);
        segmentElements.push(segment);

        const legendItem = document.createElement("li");
        legendItem.className = "visitor-devices-legend-item";
        legendItem.dataset.index = String(index);
        legendItem.tabIndex = 0;
        legendItem.innerHTML = `
            <span class="visitor-devices-swatch" style="--device-color:${color}"></span>
            <span class="visitor-devices-legend-text">
                <span class="visitor-devices-legend-label">${escapeHtml(item.label)}</span>
                <span class="visitor-devices-legend-count">${item.count.toLocaleString()} ${item.count === 1 ? "visit" : "visits"}</span>
            </span>
            <span class="visitor-devices-legend-value">${formatSharePercentage(share)}</span>`;
        legend.appendChild(legendItem);
        legendElements.push(legendItem);

        offset += share * DEVICE_CHART_CIRCUMFERENCE;

        requestAnimationFrame(() => {
            segment.setAttribute(
                "stroke-dasharray",
                `${arcLength} ${DEVICE_CHART_CIRCUMFERENCE - arcLength}`
            );
        });
    });

    const setActive = (activeIndex) => {
        segmentElements.forEach((element, index) => {
            element.classList.toggle("is-active", index === activeIndex);
            element.classList.toggle("is-dimmed", activeIndex !== null && index !== activeIndex);
        });
        legendElements.forEach((element, index) => {
            element.classList.toggle("is-active", index === activeIndex);
            element.classList.toggle("is-dimmed", activeIndex !== null && index !== activeIndex);
        });
    };

    const bindHighlight = (elements) => {
        elements.forEach((element, index) => {
            element.addEventListener("mouseenter", () => setActive(index));
            element.addEventListener("mouseleave", () => setActive(null));
            element.addEventListener("focus", () => setActive(index));
            element.addEventListener("blur", () => setActive(null));
        });
    };

    bindHighlight(segmentElements);
    bindHighlight(legendElements);
}

const SEARCH_DEBOUNCE_MS = 300;

document.addEventListener("DOMContentLoaded", async () => {
    const dashboardService = new AdminDashboardService();
    const visitorCount = document.getElementById("visitorCount");
    const botCount = document.getElementById("botCount");
    const musicCount = document.getElementById("musicCount");
    const galleryCount = document.getElementById("galleryCount");
    const videoCount = document.getElementById("videoCount");
    const keyProjectCount = document.getElementById("keyProjectCount");
    const companyRoadmapCount = document.getElementById("companyRoadmapCount");
    const lastUpdated = document.getElementById("dashboardLastUpdated");

    const summaryPromise = dashboardService.fetchSummary({ recent_limit: 0 });
    function renderSummary(summary) {
        animateCount(visitorCount, 0, Number(summary?.visitor_total_count || 0), 800);
        animateCount(botCount, 0, Number(summary?.bot_total_count || 0), 800);
        animateCount(musicCount, 0, Number(summary?.total_music || 0), 700);
        animateCount(galleryCount, 0, Number(summary?.total_gallery || 0), 700);
        animateCount(videoCount, 0, Number(summary?.total_video || 0), 700);
        animateCount(keyProjectCount, 0, Number(summary?.total_projects || 0), 700);
        animateCount(companyRoadmapCount, 0, Number(summary?.total_roadmaps || 0), 700);
        renderDeviceBreakdown(summary?.device_breakdown);
        if (lastUpdated) {
            lastUpdated.textContent = formatTimestamp();
        }
    }

    // ─── Recent Activity Table (server paginated) ───────────────────────
    (function () {
        const tableBody = document.getElementById("recentActivityTableBody");
        const perPageSelect = document.getElementById("activityPerPage");
        const searchInput = document.getElementById("activitySearchInput");
        const orderSelect = document.getElementById("activityOrderSelect");
        const prevBtn = document.getElementById("activityPrevPage");
        const nextBtn = document.getElementById("activityNextPage");
        const pageInfo = document.getElementById("activityPageInfo");

        if (!tableBody || !perPageSelect || !prevBtn || !nextBtn || !pageInfo) return;

        let activityData = [];
        let currentPage = 1;
        let total = 0;
        let requestToken = 0;
        let searchTimer = null;

        function perPageValue() {
            return Number(perPageSelect.value) || 10;
        }

        function totalPages() {
            return Math.max(1, Math.ceil(total / perPageValue()));
        }

        function activityDetails(item) {
            if (item.body) {
                try {
                    return JSON.stringify(item.body);
                } catch (error) {
                    return String(item.body);
                }
            }
            if (item.status_code) {
                return `Status: ${item.status_code}`;
            }
            return "";
        }

        function renderPage() {
            if (currentPage > totalPages()) currentPage = totalPages();

            if (total === 0) {
                tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No recent activity.</td></tr>';
                pageInfo.textContent = "";
                prevBtn.disabled = true;
                nextBtn.disabled = true;
                const clearBtn = document.getElementById("clearActivityBtn");
                if (clearBtn) clearBtn.disabled = true;
                return;
            }

            const clearBtn = document.getElementById("clearActivityBtn");
            if (clearBtn) clearBtn.disabled = false;

            const start = (currentPage - 1) * perPageValue() + 1;
            const end = start + activityData.length - 1;

            const rows = activityData.map((item) => {
                const ts = item.timestamp ? new Date(item.timestamp) : new Date();
                const user = item.user_id || item.user || "-";
                const method = item.method || "-";
                const action = item.path || item.action || "";
                const rawId = item._id;
                const rowId = (rawId && typeof rawId === "object") ? (rawId.$oid || "") : (rawId || "");
                let details = activityDetails(item);
                if (details.length > 200) details = `${details.slice(0, 200)}...`;

                return `
                    <tr data-record-id="${rowId}">
                      <td class="small text-muted">${formatTimestamp(ts)}</td>
                      <td>${user}</td>
                      <td>${method}</td>
                      <td>${action}</td>
                      <td><pre class="mb-0 small">${details}</pre></td>
                      <td>
                        <button class="btn btn-outline-danger btn-sm py-0 px-1 activity-delete-btn" title="Delete">
                          <i class="bi bi-trash"></i>
                        </button>
                      </td>
                    </tr>`;
            }).join("");

            tableBody.innerHTML = rows;
            pageInfo.textContent = `${start}-${end} of ${total}`;
            prevBtn.disabled = currentPage <= 1;
            nextBtn.disabled = currentPage >= totalPages();

            // Attach delete handlers
            tableBody.querySelectorAll(".activity-delete-btn").forEach((btn) => {
                btn.addEventListener("click", function () {
                    const row = this.closest("tr");
                    const recordId = row.dataset.recordId;
                    if (!recordId) {
                        window.notify("Delete failed.", "error");
                        return;
                    }
                    window.confirmDelete("Are you sure you want to delete this activity record?", async () => {
                        let result = null;
                        try {
                            result = await dashboardService.deleteActivity([recordId]);
                        } catch (_) {
                            window.notify("Delete failed.", "error");
                            return;
                        }

                        const json = result.data;
                        if (!result.ok) {
                            window.notify((json && json.message) || "Delete failed.", "error");
                            return;
                        }

                        if (json && json.ok) {
                            const modalEl = document.getElementById("deleteConfirmModal");
                            if (modalEl && window.bootstrap && window.bootstrap.Modal) {
                                const instance = window.bootstrap.Modal.getInstance(modalEl);
                                if (instance) instance.hide();
                            }
                            window.notify(json.message || "Record deleted.", "success");
                            loadActivity();
                        } else {
                            window.notify((json && json.message) || "Delete failed.", "error");
                        }
                    });
                });
            });
        }

        async function loadActivity() {
            const token = ++requestToken;
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center">Loading...</td></tr>';
            try {
                const json = await dashboardService.fetchRecentActivity({
                    page: currentPage,
                    perPage: perPageValue(),
                    order: orderSelect?.value || "desc",
                    search: String(searchInput?.value || "").trim(),
                });
                if (token !== requestToken) return;
                activityData = Array.isArray(json?.data) ? json.data : [];
                total = Number(json?.total || 0);
                renderPage();
            } catch (err) {
                if (token !== requestToken) return;
                console.error("Failed to load recent activity", err);
                activityData = [];
                total = 0;
                renderPage();
            }
        }

        perPageSelect.addEventListener("change", () => {
            currentPage = 1;
            loadActivity();
        });
        searchInput?.addEventListener("input", () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                currentPage = 1;
                loadActivity();
            }, SEARCH_DEBOUNCE_MS);
        });
        orderSelect?.addEventListener("change", () => {
            currentPage = 1;
            loadActivity();
        });
        document.getElementById("clearActivityBtn")?.addEventListener("click", () => {
            window.confirmDelete("Clear all recent activity records?", async () => {
                const result = await dashboardService.clearAllActivity();
                const json = result.data;
                if (json && json.ok) {
                    bootstrap.Modal.getInstance(document.getElementById("deleteConfirmModal")).hide();
                    window.notify(json.message || "All activity cleared.", "success");
                    currentPage = 1;
                    loadActivity();
                } else {
                    window.notify((json && json.message) || "Failed to clear activity.", "error");
                }
            });
        });
        prevBtn.addEventListener("click", () => {
            if (currentPage > 1) {
                currentPage--;
                loadActivity();
            }
        });
        nextBtn.addEventListener("click", () => {
            if (currentPage < totalPages()) {
                currentPage++;
                loadActivity();
            }
        });

        loadActivity();
    })();

    // ─── Visits Table (server paginated) ────────────────────────────────
    (function () {
        const tableBody = document.getElementById("visitsTableBody");
        const perPageSelect = document.getElementById("visitsPerPage");
        const searchInput = document.getElementById("visitsSearchInput");
        const orderSelect = document.getElementById("visitsOrderSelect");
        const prevBtn = document.getElementById("visitsPrevPage");
        const nextBtn = document.getElementById("visitsNextPage");
        const pageInfo = document.getElementById("visitsPageInfo");

        if (!tableBody) return;

        let visitsData = [];
        let currentPage = 1;
        let total = 0;
        let requestToken = 0;
        let searchTimer = null;

        function perPageValue() {
            return Number(perPageSelect?.value) || 10;
        }

        function totalPages() {
            return Math.max(1, Math.ceil(total / perPageValue()));
        }

        function renderPage() {
            if (currentPage > totalPages()) currentPage = totalPages();

            if (total === 0) {
                tableBody.innerHTML = '<tr><td colspan="11" class="text-center text-muted">No visit records found.</td></tr>';
                pageInfo.textContent = "";
                prevBtn.disabled = true;
                nextBtn.disabled = true;
                const clearBtn = document.getElementById("clearVisitsBtn");
                if (clearBtn) clearBtn.disabled = true;
                return;
            }

            const clearBtn = document.getElementById("clearVisitsBtn");
            if (clearBtn) clearBtn.disabled = false;

            const start = (currentPage - 1) * perPageValue() + 1;
            const end = start + visitsData.length - 1;

            const rows = visitsData.map((item) => {
                const tsText = formatVisitTimestamp(item);
                const ip = item.ip_address || "Unknown";
                const _id = item._id?.$oid || item._id || "";
                return `
                    <tr data-record-id="${_id}">
                        <td>${item.system || "-"}</td>
                        <td>${item.device || "-"}</td>
                        <td>${item.browser || "-"}</td>
                        <td>${item.os || "-"}</td>
                        <td>${formatSiteLabel(item)}</td>
                        <td>${item.page || "-"}</td>
                        <td>${ip}</td>
                        <td>${item.city || "-"}</td>
                        <td>${item.country || "-"}</td>
                        <td class="small text-muted">${tsText}</td>
                        <td>
                            <button class="btn btn-outline-danger btn-sm py-0 px-1 visit-delete-btn"
                                title="Delete">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>`;
            }).join("");

            tableBody.innerHTML = rows;
            pageInfo.textContent = `${start}-${end} of ${total}`;
            prevBtn.disabled = currentPage <= 1;
            nextBtn.disabled = currentPage >= totalPages();

            // Attach delete handlers
            tableBody.querySelectorAll(".visit-delete-btn").forEach((btn) => {
                btn.addEventListener("click", function () {
                    const row = this.closest("tr");
                    const recordId = row.dataset.recordId;
                    window.confirmDelete("Are you sure you want to delete this visit record?", async () => {
                        const result = await dashboardService.deleteVisit(recordId);
                        const json = result.data;
                        if (json && json.ok) {
                            bootstrap.Modal.getInstance(document.getElementById("deleteConfirmModal")).hide();
                            window.notify("Record deleted.", "success");
                            loadVisits();
                        } else {
                            window.notify((json && json.message) || "Delete failed.", "error");
                        }
                    });
                });
            });
        }

        async function loadVisits() {
            const token = ++requestToken;
            tableBody.innerHTML = '<tr><td colspan="11" class="text-center">Loading...</td></tr>';
            try {
                const json = await dashboardService.fetchVisits({
                    page: currentPage,
                    perPage: perPageValue(),
                    order: orderSelect?.value || "desc",
                    search: String(searchInput?.value || "").trim(),
                });
                if (token !== requestToken) return;
                visitsData = Array.isArray(json?.data) ? json.data : [];
                total = Number(json?.total || 0);
                renderPage();
            } catch (err) {
                if (token !== requestToken) return;
                console.error("Failed to load visits", err);
                visitsData = [];
                total = 0;
                renderPage();
            }
        }

        perPageSelect?.addEventListener("change", () => {
            currentPage = 1;
            loadVisits();
        });
        searchInput?.addEventListener("input", () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                currentPage = 1;
                loadVisits();
            }, SEARCH_DEBOUNCE_MS);
        });
        orderSelect?.addEventListener("change", () => {
            currentPage = 1;
            loadVisits();
        });
        document.getElementById("clearVisitsBtn")?.addEventListener("click", () => {
            window.confirmDelete("Clear all visitor records?", async () => {
                const result = await dashboardService.clearAllVisitors();
                const json = result.data;
                if (json && json.ok) {
                    bootstrap.Modal.getInstance(document.getElementById("deleteConfirmModal")).hide();
                    window.notify(json.message || "All visitors cleared.", "success");
                    currentPage = 1;
                    loadVisits();
                } else {
                    window.notify((json && json.message) || "Failed to clear visitors.", "error");
                }
            });
        });
        prevBtn.addEventListener("click", () => {
            if (currentPage > 1) {
                currentPage--;
                loadVisits();
            }
        });
        nextBtn.addEventListener("click", () => {
            if (currentPage < totalPages()) {
                currentPage++;
                loadVisits();
            }
        });

        loadVisits();
    })();

    try {
        renderSummary(await summaryPromise);
    } catch (err) {
        console.error("Dashboard Error:", err);
        if (lastUpdated) lastUpdated.textContent = formatTimestamp();
    }
});
