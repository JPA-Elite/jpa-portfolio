// repositories/VisitRepository.js
import { IVisitRepository } from "../interfaces/IVisitRepository.js";

export class VisitRepository extends IVisitRepository {
    constructor(baseUrl = "/admin/api/visits") {
        super();
        this.baseUrl = baseUrl;
    }

    /**
     * Fetch total visits from API endpoint
     * @returns {Promise<number>}
     */
    async fetchVisitCount() {
        try {
            const response = await fetch(`${this.baseUrl}/info`);
            if (!response.ok) throw new Error("Failed to fetch visit count");

            const data = await response.json();
            return data.count || 0;
        } catch (error) {
            console.error("VisitRepository Error:", error);
            throw error;
        }
    }
}
