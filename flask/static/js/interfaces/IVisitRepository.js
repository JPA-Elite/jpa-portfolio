// interfaces/IVisitRepository.js

/**
 * @interface IVisitRepository
 * Defines the methods for accessing visit data from the API.
 */
export class IVisitRepository {
    /**
     * Fetch total visit count from the server.
     * @returns {Promise<any>} Resolves with the total visit count.
     */
    async fetchVisitCount() {
        throw new Error("Method 'fetchVisitCount()' must be implemented.");
    }
}
