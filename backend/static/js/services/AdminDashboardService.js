// services/AdminDashboardService.js
import { AdminDashboardRepository } from "../repositories/AdminDashboardRepository.js";

export class AdminDashboardService {
    constructor() {
        /** @type {import("../interfaces/IAdminDashboardRepository.js").IAdminDashboardRepository} */
        this.repository = new AdminDashboardRepository();
    }

    async fetchSummary() {
        try {
            return await this.repository.fetchSummary();
        } catch (error) {
            console.error("AdminDashboardService Error:", error);
            throw error;
        }
    }

    async fetchRecentActivity() {
        try {
            return await this.repository.fetchRecentActivity();
        } catch (error) {
            console.error("AdminDashboardService Error:", error);
            throw error;
        }
    }
}
