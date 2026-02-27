// pages/dashboard.js
import { VisitService } from "../../services/VisitService.js";

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
    const visitService = new VisitService();
    const visitorCount = document.getElementById("visitorCount");
    const botCount = document.getElementById("botCount");
    const musicCount = document.getElementById("musicCount");
    const galleryCount = document.getElementById("galleryCount");
    const videoCount = document.getElementById("videoCount");
    const keyProjectCount = document.getElementById("keyProjectCount");
    const companyRoadmapCount = document.getElementById("companyRoadmapCount");
    const lastUpdated = document.getElementById("dashboardLastUpdated");

    try {
        const res = await fetch('/admin/api/dashboard-summary');
        if (!res.ok) throw new Error('Failed to fetch dashboard summary');
        const summary = await res.json();

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
        const prevBtn = document.getElementById("activityPrevPage");
        const nextBtn = document.getElementById("activityNextPage");
        const pageInfo = document.getElementById("activityPageInfo");

        if (!tableBody || !perPageSelect || !prevBtn || !nextBtn || !pageInfo) return;

        let activityData = [];
        let currentPage = 1;

        function renderPage() {
            const perPage = Number(perPageSelect.value) || 10;
            const total = activityData.length;
            const totalPages = Math.max(1, Math.ceil(total / perPage));
            if (currentPage > totalPages) currentPage = totalPages;
            const start = (currentPage - 1) * perPage;
            const end = Math.min(total, start + perPage);

            if (total === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No recent activity.</td></tr>';
                pageInfo.textContent = '';
                return;
            }

            const rows = activityData.slice(start, end).map(item => {
                const ts = item.timestamp ? new Date(item.timestamp) : new Date();
                const user = item.user_id || item.user || '—';
                const method = item.method || '—';
                const action = item.path || item.action || '';
                let details = '';
                if (item.body) {
                    try { details = JSON.stringify(item.body); } catch (e) { details = String(item.body); }
                } else if (item.status_code) {
                    details = `Status: ${item.status_code}`;
                }
                // truncate details
                if (details.length > 200) details = details.slice(0, 200) + '...';
                return `\n                    <tr>\n                      <td class="small text-muted">${formatTimestamp(ts)}</td>\n                      <td>${user}</td>\n                      <td>${method}</td>\n                      <td>${action}</td>\n                      <td><pre class="mb-0 small">${details}</pre></td>\n                    </tr>`;
            }).join('');

            tableBody.innerHTML = rows;
            pageInfo.textContent = `${start + 1}-${end} of ${total}`;
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
                    const res = await fetch('/admin/api/recent-activity');
                    if (!res.ok) {
                        activityData = [];
                        renderPage();
                        return;
                    }
                    const data = await res.json();
                    if (!Array.isArray(data)) activityData = [];
                    else activityData = data;
                    currentPage = 1;
                    renderPage();
                } catch (err) {
                    console.error('Failed to load recent activity', err);
                    activityData = [];
                    renderPage();
                }
        }

        perPageSelect.addEventListener('change', () => { currentPage = 1; renderPage(); });
        prevBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderPage(); } });
        nextBtn.addEventListener('click', () => { const perPage = Number(perPageSelect.value)||10; const totalPages = Math.max(1, Math.ceil(activityData.length / perPage)); if (currentPage < totalPages) { currentPage++; renderPage(); } });

        loadActivity();
    })();
});
