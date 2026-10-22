import { AdminFaceRepository } from "../repositories/AdminFaceRepository.js";

export class AdminFaceService {
    constructor() {
        /** @type {import("../interfaces/IAdminFaceRepository.js").IAdminFaceRepository} */
        this.repository = new AdminFaceRepository();
    }

    async register(frames) {
        try {
            return this.toPayload(await this.repository.register(frames), "Failed to register face.");
        } catch (error) {
            console.error("AdminFaceService Error:", error);
            throw error;
        }
    }

    async verify(frames) {
        try {
            return this.toPayload(await this.repository.verify(frames), "Failed to verify face.");
        } catch (error) {
            console.error("AdminFaceService Error:", error);
            throw error;
        }
    }

    toPayload(result, fallback) {
        if (!result.ok || !result.data || result.data.ok !== true) {
            const message = (result.data && result.data.message) || fallback;
            throw new Error(message);
        }

        return result.data;
    }
}
