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
}
