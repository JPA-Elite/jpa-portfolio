// services/VisitorService.js
import { VisitorRepository } from "../repositories/VisitorRepository.js";

export class VisitorService {
    constructor() {
        /** @type {import("../interfaces/IVisitorRepository.js").IVisitorRepository} */
        this.repository = new VisitorRepository();
    }

    async deletePageSystemInfo(records) {
        try {
            return await this.repository.deletePageSystemInfo(records);
        } catch (error) {
            console.error("VisitorService Error:", error);
            throw error;
        }
    }
}
