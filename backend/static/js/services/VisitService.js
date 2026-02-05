// services/VisitService.js
import { VisitRepository } from "../repositories/VisitRepository.js";
import { EMPTY_VISIT_COUNTS, normalizeVisitCount } from "../utils/visit.js";

export class VisitService {
    constructor() {
        /** @type {import("../interfaces/IVisitRepository.js").IVisitRepository} */
        this.repository = new VisitRepository();
    }

    /**
     * Get total visits with fallback values.
     * @returns {Promise<{visitor_total_count: number, bot_total_count: number}>}
     */
    async getVisitCount() {
        try {
            const count = await this.repository.fetchVisitCount();
            return normalizeVisitCount(count);
        } catch (error) {
            console.error("VisitService Error:", error);
            return EMPTY_VISIT_COUNTS;
        }
    }
}
