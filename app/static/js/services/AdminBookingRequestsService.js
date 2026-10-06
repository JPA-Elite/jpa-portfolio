import { AdminBookingRequestsRepository } from "../repositories/AdminBookingRequestsRepository.js";

export class AdminBookingRequestsService {
    constructor() {
        this.repository = new AdminBookingRequestsRepository();
    }

    async fetchList(options) {
        try {
            return await this.repository.fetchList(options);
        } catch (error) {
            console.error("AdminBookingRequestsService Error:", error);
            throw error;
        }
    }

    async remove(id) {
        return this.#toResult(this.repository.remove(id));
    }

    async clearAll() {
        return this.#toResult(this.repository.clearAll());
    }

    async #toResult(responsePromise) {
        try {
            const response = await responsePromise;
            let data = null;
            try { data = await response.json(); } catch (e) { data = null; }
            return { ok: response.ok, data };
        } catch (error) {
            console.error("AdminBookingRequestsService Error:", error);
            throw error;
        }
    }
}
