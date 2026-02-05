// services/SystemInfoService.js
import { SystemInfoRepository } from "../repositories/SystemInfoRepository.js";

export class SystemInfoService {
    constructor() {
        /** @type {import("../interfaces/ISystemInfoRepository.js").ISystemInfoRepository} */
        this.repository = new SystemInfoRepository();
    }

    /**
     * @param {Array<{_id?: string, image_capture?: string | null}>} records
     * @returns {Promise<{status: string, message: string}>}
     */
    async clearPageSystemInfo(records) {
        try {
            const data = await this.repository.deletePageSystemInfo(records);

            return {
                status: data?.status ?? "error",
                message: data?.message ?? "Unable to clear data.",
            };
        } catch (error) {
            console.error("SystemInfoService Error:", error);
            return {
                status: "error",
                message: "Unable to clear data.",
            };
        }
    }
}
