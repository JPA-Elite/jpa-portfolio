// repositories/AdminLoginAttemptsRepository.js
import { IAdminLoginAttemptsRepository } from "../interfaces/IAdminLoginAttemptsRepository.js";

export class AdminLoginAttemptsRepository extends IAdminLoginAttemptsRepository {
    constructor(baseUrl = "/admin/api") {
        super();
        this.baseUrl = baseUrl;
    }

    async fetchClientIp() {
        const response = await fetch(`${this.baseUrl}/get-client-ip`);
        if (!response.ok) {
            throw new Error("Failed to fetch client IP");
        }
        return response.json();
    }

    async fetchList({ page = 1, perPage = 10, order = "desc", search = "" } = {}) {
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

        const response = await fetch(
            `${this.baseUrl}/login-attempts?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error("Failed to fetch login attempts");
        }

        return response.json();
    }

    async remove(id) {
        return fetch(`${this.baseUrl}/delete-login-attempt/${id}`, {
            method: "DELETE",
        });
    }
}
