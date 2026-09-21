// interfaces/IAdminDashboardRepository.js

export class IAdminDashboardRepository {
    async fetchSummary() {
        throw new Error("Method 'fetchSummary()' must be implemented.");
    }

    async fetchRecentActivity(params) {
        throw new Error("Method 'fetchRecentActivity()' must be implemented.");
    }

    async fetchVisits(params) {
        throw new Error("Method 'fetchVisits()' must be implemented.");
    }
}
