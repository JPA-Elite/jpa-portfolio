// services/AdminSettingsService.js
import { AdminSettingsRepository } from "../repositories/AdminSettingsRepository.js";

export class AdminSettingsService {
    constructor() {
        /** @type {import("../interfaces/IAdminSettingsRepository.js").IAdminSettingsRepository} */
        this.repository = new AdminSettingsRepository();
    }

    async updateProfile(formData) {
        return this.#toResult(this.repository.updateProfile(formData));
    }

    async #toResult(responsePromise) {
        try {
            const response = await responsePromise;
            let data = null;
            try {
                data = await response.json();
            } catch (parseError) {
                data = null;
            }
            return { ok: response.ok, data };
        } catch (error) {
            console.error("AdminSettingsService Error:", error);
            throw error;
        }
    }
}
