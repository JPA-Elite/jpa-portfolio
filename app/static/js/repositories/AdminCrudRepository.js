// repositories/AdminCrudRepository.js
import { IAdminCrudRepository } from "../interfaces/IAdminCrudRepository.js";

export class AdminCrudRepository extends IAdminCrudRepository {
    constructor(resource, baseUrl = "/admin/api") {
        super();
        this.resource = resource;
        this.baseUrl = baseUrl;
    }

    async fetchList(options = {}) {
        const {
            page = 1,
            perPage = 10,
            order = "desc",
            search = "",
            ...extraParams
        } = options;
        const params = new URLSearchParams();
        params.set("page", String(page));
        params.set("per_page", String(perPage));
        if (order) {
            params.set("order", order);
        }
        const normalizedSearch = String(search || "").trim();
        if (normalizedSearch) {
            params.set("search", normalizedSearch);
        }
        Object.entries(extraParams).forEach(([key, value]) => {
            if (value === undefined || value === null) {
                return;
            }
            const normalized = String(value).trim();
            if (!normalized) {
                return;
            }
            params.set(key, normalized);
        });

        const response = await fetch(
            `${this.baseUrl}/${this.resource}-list?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(`Failed to fetch ${this.resource} list`);
        }

        return response.json();
    }

    async add(formData) {
        return fetch(`${this.baseUrl}/add-${this.resource}`, {
            method: "POST",
            body: formData,
        });
    }

    async update(id, formData) {
        return fetch(`${this.baseUrl}/update-${this.resource}/${id}`, {
            method: "PUT",
            body: formData,
        });
    }

    async remove(id) {
        return fetch(`${this.baseUrl}/delete-${this.resource}/${id}`, {
            method: "DELETE",
        });
    }
}
