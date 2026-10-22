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

    async deleteActivity(recordIds) {
        try {
            return await this.repository.deleteActivity(recordIds);
        } catch (error) {
            console.error("AdminDashboardService Error:", error);
            throw error;
        }
    }

    async clearAllActivity() {
        try {
            return await this.repository.clearAllActivity();
        } catch (error) {
            console.error("AdminDashboardService Error:", error);
            throw error;
        }
    }

    async deleteVisit(recordId) {
        try {
            return await this.repository.deleteVisit(recordId);
        } catch (error) {
            console.error("AdminDashboardService Error:", error);
            throw error;
        }
    }

    async clearAllVisitors() {
        try {
            return await this.repository.clearAllVisitors();
        } catch (error) {
            console.error("AdminDashboardService Error:", error);
            throw error;
        }
    }
}
