// services/AdminDashboardService.js
import { AdminDashboardRepository } from "../repositories/AdminDashboardRepository.js";

export class AdminDashboardService {
    constructor() {
        /** @type {import("../interfaces/IAdminDashboardRepository.js").IAdminDashboardRepository} */
        this.repository = new AdminDashboardRepository();
    }

    async fetchSummary(params = { recent_limit: 0 }) {
        try {
            return await this.repository.fetchSummary(params);
        } catch (error) {
            console.error("AdminDashboardService Error:", error);
            throw error;
        }
    }

    async fetchRecentActivity(params) {
        try {
            return await this.repository.fetchRecentActivity(params);
        } catch (error) {
            console.error("AdminDashboardService Error:", error);
            throw error;
        }
    }

    async fetchVisits(params) {
        try {
            return await this.repository.fetchVisits(params);
        } catch (error) {
            console.error("AdminDashboardService Error:", error);
            throw error;
        }
    }
}
