// repositories/AdminDashboardRepository.js
import { IAdminDashboardRepository } from "../interfaces/IAdminDashboardRepository.js";

export class AdminDashboardRepository extends IAdminDashboardRepository {
    constructor(baseUrl = "/admin/api") {
        super();
        this.baseUrl = baseUrl;
    }

    async fetchSummary({ recent_limit = 0 } = {}) {
        const params = new URLSearchParams({ recent_limit });
        const response = await fetch(`${this.baseUrl}/dashboard-summary?${params.toString()}`);
        if (!response.ok) {
            throw new Error("Failed to fetch dashboard summary");
        }
        return response.json();
    }

    async fetchRecentActivity({ page = 1, perPage = 10, order = "desc", search = "" } = {}) {
        const params = new URLSearchParams({ page, perPage, order, search });
        const response = await fetch(`${this.baseUrl}/recent-activity?${params.toString()}`);
        if (!response.ok) {
            throw new Error("Failed to fetch recent activity");
        }
        return response.json();
    }

    async fetchVisits({ page = 1, perPage = 10, order = "desc", search = "" } = {}) {
        const params = new URLSearchParams({ page, perPage, order, search });
        const response = await fetch(`${this.baseUrl}/visits-list?${params.toString()}`);
        if (!response.ok) {
            throw new Error("Failed to fetch visits");
        }
        return response.json();
    }

    async request(path, options) {
        const response = await fetch(`${this.baseUrl}${path}`, options);
        let data = null;
        try {
            data = await response.json();
        } catch (error) {
            data = null;
        }
        return { ok: response.ok, status: response.status, data };
    }

    async deleteActivity(recordIds) {
        return this.request("/delete-activity", {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ record_ids: recordIds }),
        });
    }

    async clearAllActivity() {
        return this.request("/clear-all-activity", { method: "DELETE" });
    }

    async deleteVisit(recordId) {
        return this.request(`/delete-visits/${recordId}`, { method: "DELETE" });
    }

    async clearAllVisitors() {
        return this.request("/clear-all-visitors", { method: "DELETE" });
    }
}
