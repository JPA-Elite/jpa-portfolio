// services/VisitService.js
import { VisitRepository } from "../repositories/VisitRepository.js";

export class VisitService {
    constructor() {
        /** @type {import("../interfaces/IVisitRepository.js").IVisitRepository} */
        this.repository = new VisitRepository();
    }

    /**
     * Get total visits (handles logic, fallback, etc.)
     * @returns {Promise<number>}
     */
    async getVisitCount() {
        try {
            const count = await this.repository.fetchVisitCount();
            return count;
        } catch (error) {
            console.error("VisitService Error:", error);
            return 0; // fallback value
        }
    }
}
