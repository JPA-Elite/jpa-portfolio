import { IAdminBookingRequestsRepository } from "../interfaces/IAdminBookingRequestsRepository.js";

export class AdminBookingRequestsRepository extends IAdminBookingRequestsRepository {
    constructor(baseUrl = "/admin/api") {
        super();
        this.baseUrl = baseUrl;
    }

    async fetchList({ page = 1, perPage = 10, order = "desc", search = "" } = {}) {
        const params = new URLSearchParams();
        params.set("page", String(page));
        params.set("per_page", String(perPage));
        if (order) params.set("order", order);
        const normalizedSearch = String(search || "").trim();
        if (normalizedSearch) params.set("search", normalizedSearch);

        const response = await fetch(`${this.baseUrl}/booking-requests?${params.toString()}`);
        if (!response.ok) throw new Error("Failed to fetch booking requests");
        return response.json();
    }

    async remove(id) {
        return fetch(`${this.baseUrl}/delete-booking-request/${id}`, { method: "DELETE" });
    }
}
