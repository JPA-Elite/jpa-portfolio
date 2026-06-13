// services/AdminCrudService.js
import { AdminCrudRepository } from "../repositories/AdminCrudRepository.js";

export class AdminCrudService {
    constructor(resource) {
        /** @type {import("../interfaces/IAdminCrudRepository.js").IAdminCrudRepository} */
        this.repository = new AdminCrudRepository(resource);
    }

    async fetchList(options) {
        try {
            return await this.repository.fetchList(options);
        } catch (error) {
            console.error("AdminCrudService Error:", error);
            throw error;
        }
    }

    async add(formData) {
        return this.#toResult(this.repository.add(formData));
    }

    async update(id, formData) {
        return this.#toResult(this.repository.update(id, formData));
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
            console.error("AdminCrudService Error:", error);
            throw error;
        }
    }
}
