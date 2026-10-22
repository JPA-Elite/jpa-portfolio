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

    async deleteActivity(recordIds) {
        throw new Error("Method 'deleteActivity()' must be implemented.");
    }

    async clearAllActivity() {
        throw new Error("Method 'clearAllActivity()' must be implemented.");
    }

    async deleteVisit(recordId) {
        throw new Error("Method 'deleteVisit()' must be implemented.");
    }

    async clearAllVisitors() {
        throw new Error("Method 'clearAllVisitors()' must be implemented.");
    }
}
