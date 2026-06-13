// repositories/AdminSettingsRepository.js
import { IAdminSettingsRepository } from "../interfaces/IAdminSettingsRepository.js";

export class AdminSettingsRepository extends IAdminSettingsRepository {
    constructor(baseUrl = "/admin/api") {
        super();
        this.baseUrl = baseUrl;
    }

    async updateProfile(formData) {
        return fetch(`${this.baseUrl}/update-profile`, {
            method: "POST",
            body: formData,
        });
    }
}
