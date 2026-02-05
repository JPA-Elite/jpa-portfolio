// repositories/VisitRepository.js
import { IVisitRepository } from "../interfaces/IVisitRepository.js";

export class VisitRepository extends IVisitRepository {
    constructor(baseUrl = "/admin/api/visits") {
        super();
        this.baseUrl = baseUrl;
    }

    /**
     * Fetch total visits from API endpoint.
     * @returns {Promise<{visitor_total_count?: number, bot_total_count?: number}>}
     */
    async fetchVisitCount() {
        const response = await fetch(`${this.baseUrl}/info`);

        if (!response.ok) {
            throw new Error("Failed to fetch visit count");
        }

        return response.json();
    }
}
