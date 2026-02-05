// repositories/SystemInfoRepository.js
import { ISystemInfoRepository } from "../interfaces/ISystemInfoRepository.js";

export class SystemInfoRepository extends ISystemInfoRepository {
    constructor(baseUrl = "/api/delete-page-system-info") {
        super();
        this.baseUrl = baseUrl;
    }

    /**
     * @param {Array<{_id?: string, image_capture?: string | null}>} records
     * @returns {Promise<{status?: string, message?: string}>}
     */
    async deletePageSystemInfo(records) {
        const response = await fetch(this.baseUrl, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ records }),
        });

        if (!response.ok) {
            throw new Error("Failed to clear page system info");
        }

        return response.json();
    }
}
