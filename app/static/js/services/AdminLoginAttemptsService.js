// services/AdminLoginAttemptsService.js
import { AdminLoginAttemptsRepository } from "../repositories/AdminLoginAttemptsRepository.js";

export class AdminLoginAttemptsService {
    constructor() {
        /** @type {import("../interfaces/IAdminLoginAttemptsRepository.js").IAdminLoginAttemptsRepository} */
        this.repository = new AdminLoginAttemptsRepository();
    }

    async fetchClientIp() {
        try {
            return await this.repository.fetchClientIp();
        } catch (error) {
            console.error("AdminLoginAttemptsService Error:", error);
            throw error;
        }
    }

    async fetchList(options) {
        try {
            return await this.repository.fetchList(options);
        } catch (error) {
            console.error("AdminLoginAttemptsService Error:", error);
            throw error;
        }
    }

    async remove(id) {
        return this.#toResult(this.repository.remove(id));
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
            console.error("AdminLoginAttemptsService Error:", error);
            throw error;
        }
    }
}
