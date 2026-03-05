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

function formatTimestamp(date = new Date()) {
    return date.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}

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

    try {
        const summary = await dashboardService.fetchSummary();

        animateCount(visitorCount, 0, Number(summary?.visitor_total_count || 0), 800);
        animateCount(botCount, 0, Number(summary?.bot_total_count || 0), 800);
        animateCount(musicCount, 0, Number(summary?.total_music || 0), 700);
        animateCount(galleryCount, 0, Number(summary?.total_gallery || 0), 700);
        animateCount(videoCount, 0, Number(summary?.total_video || 0), 700);
        animateCount(keyProjectCount, 0, Number(summary?.total_projects || 0), 700);
        animateCount(companyRoadmapCount, 0, Number(summary?.total_roadmaps || 0), 700);

        if (lastUpdated) {
            lastUpdated.textContent = formatTimestamp();
        }

        if (summary?.recent_activity && Array.isArray(summary.recent_activity)) {
            window.__dashboard_recent_activity = summary.recent_activity;
        }

    } catch (err) {
        console.error("Dashboard Error:", err);
        if (lastUpdated) lastUpdated.textContent = formatTimestamp();
    }

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

        function getFilteredActivityData() {
            const searchValue = String(searchInput?.value || "").trim().toLowerCase();
            const filtered = !searchValue
                ? [...activityData]
                : activityData.filter((item) => {
                    let details = "";
                    if (item.body) {
                        try {
                            details = JSON.stringify(item.body);
                        } catch (error) {
                            details = String(item.body);
                        }
                    } else if (item.status_code) {
                        details = `Status: ${item.status_code}`;
                    }

                    const searchable = [
                        item.timestamp || "",
                        item.user_id || item.user || "",
                        item.method || "",
                        item.path || item.action || "",
                        details || "",
                    ].join(" ").toLowerCase();

                    return searchable.includes(searchValue);
                });

            const order = String(orderSelect?.value || "desc").toLowerCase();
            filtered.sort((a, b) => {
                const aTime = new Date(a.timestamp || 0).getTime() || 0;
                const bTime = new Date(b.timestamp || 0).getTime() || 0;
                return order === "asc" ? aTime - bTime : bTime - aTime;
            });

            return filtered;
        }

        function renderPage() {
            const filteredData = getFilteredActivityData();
            const perPage = Number(perPageSelect.value) || 10;
            const total = filteredData.length;
            const totalPages = Math.max(1, Math.ceil(total / perPage));
            if (currentPage > totalPages) currentPage = totalPages;
            const start = (currentPage - 1) * perPage;
            const end = Math.min(total, start + perPage);
            const atFirstPage = currentPage <= 1;
            const atLastPage = currentPage >= totalPages;

            if (total === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No recent activity.</td></tr>';
                pageInfo.textContent = "";
                prevBtn.disabled = true;
                nextBtn.disabled = true;
                return;
            }

            const rows = filteredData.slice(start, end).map((item) => {
                const ts = item.timestamp ? new Date(item.timestamp) : new Date();
                const user = item.user_id || item.user || "-";
                const method = item.method || "-";
                const action = item.path || item.action || "";
                let details = "";
                if (item.body) {
                    try {
                        details = JSON.stringify(item.body);
                    } catch (error) {
                        details = String(item.body);
                    }
                } else if (item.status_code) {
                    details = `Status: ${item.status_code}`;
                }
                if (details.length > 200) details = `${details.slice(0, 200)}...`;

                return `
                    <tr>
                      <td class="small text-muted">${formatTimestamp(ts)}</td>
                      <td>${user}</td>
                      <td>${method}</td>
                      <td>${action}</td>
                      <td><pre class="mb-0 small">${details}</pre></td>
                    </tr>`;
            }).join("");

            tableBody.innerHTML = rows;
            pageInfo.textContent = `${start + 1}-${end} of ${total}`;
            prevBtn.disabled = atFirstPage;
            nextBtn.disabled = atLastPage;
        }

        async function loadActivity() {
            tableBody.innerHTML = '<tr><td colspan="5" class="text-center">Loading...</td></tr>';
            if (window.__dashboard_recent_activity && Array.isArray(window.__dashboard_recent_activity)) {
                activityData = window.__dashboard_recent_activity;
                currentPage = 1;
                renderPage();
                return;
            }

            try {
                const data = await dashboardService.fetchRecentActivity();
                activityData = Array.isArray(data) ? data : [];
                currentPage = 1;
                renderPage();
            } catch (err) {
                console.error("Failed to load recent activity", err);
                activityData = [];
                renderPage();
            }
        }

        perPageSelect.addEventListener("change", () => {
            currentPage = 1;
            renderPage();
        });
        searchInput?.addEventListener("input", () => {
            currentPage = 1;
            renderPage();
        });
        orderSelect?.addEventListener("change", () => {
            currentPage = 1;
            renderPage();
        });
        prevBtn.addEventListener("click", () => {
            if (currentPage > 1) {
                currentPage--;
                renderPage();
            }
        });
        nextBtn.addEventListener("click", () => {
            const perPage = Number(perPageSelect.value) || 10;
            const totalPages = Math.max(1, Math.ceil(getFilteredActivityData().length / perPage));
            if (currentPage < totalPages) {
                currentPage++;
                renderPage();
            }
        });

        loadActivity();
    })();
});
