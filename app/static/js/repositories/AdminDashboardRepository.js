// repositories/AdminDashboardRepository.js
import { IAdminDashboardRepository } from "../interfaces/IAdminDashboardRepository.js";

export class AdminDashboardRepository extends IAdminDashboardRepository {
    constructor(baseUrl = "/admin/api") {
        super();
        this.baseUrl = baseUrl;
    }

    async fetchSummary() {
        const response = await fetch(`${this.baseUrl}/dashboard-summary`);
        if (!response.ok) {
            throw new Error("Failed to fetch dashboard summary");
        }
        return response.json();
    }

    async fetchRecentActivity() {
        const response = await fetch(`${this.baseUrl}/recent-activity`);
        if (!response.ok) {
            throw new Error("Failed to fetch recent activity");
        }
        return response.json();
    }
}
