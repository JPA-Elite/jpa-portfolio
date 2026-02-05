// interfaces/IVisitRepository.js

/**
 * @interface IVisitRepository
 * Defines methods for accessing visit data from the API.
 */
export class IVisitRepository {
    /**
     * Fetch total visit counts from the server.
     * @returns {Promise<{visitor_total_count?: number, bot_total_count?: number}>}
     */
    async fetchVisitCount() {
        throw new Error("Method 'fetchVisitCount()' must be implemented.");
    }
}
