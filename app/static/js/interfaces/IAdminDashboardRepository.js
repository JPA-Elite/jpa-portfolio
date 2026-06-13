// interfaces/IAdminDashboardRepository.js

export class IAdminDashboardRepository {
    async fetchSummary() {
        throw new Error("Method 'fetchSummary()' must be implemented.");
    }

    async fetchRecentActivity() {
        throw new Error("Method 'fetchRecentActivity()' must be implemented.");
    }
}
