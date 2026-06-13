// repositories/VisitorRepository.js
import { IVisitorRepository } from "../interfaces/IVisitorRepository.js";

export class VisitorRepository extends IVisitorRepository {
    constructor(baseUrl = "/api/delete-page-system-info") {
        super();
        this.baseUrl = baseUrl;
    }

    async deletePageSystemInfo(records) {
        const response = await fetch(this.baseUrl, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ records }),
        });

        if (!response.ok) {
            throw new Error("Failed to delete page system info");
        }

        return response.json();
    }
}
