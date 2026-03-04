// repositories/VlogLikeRepository.js
import { IVlogLikeRepository } from "../interfaces/IVlogLikeRepository.js";

export class VlogLikeRepository extends IVlogLikeRepository {
    constructor(baseUrl = "/api/vlog-like") {
        super();
        this.baseUrl = baseUrl;
    }

    async toggleLike(vlogId) {
        const formData = new FormData();
        formData.append("vlog_id", JSON.stringify(vlogId));

        const response = await fetch(this.baseUrl, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error("Failed to toggle vlog like");
        }

        return response.json();
    }

    async fetchCountsBatch(vlogIds) {
        const params = new URLSearchParams();
        params.set("vlog_ids", vlogIds.join(","));

        const response = await fetch(
            `${this.baseUrl}/counts/batch?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error("Failed to fetch vlog counts");
        }

        return response.json();
    }

    async fetchCounts(vlogId) {
        const response = await fetch(
            `${this.baseUrl}/counts?vlog_id=${encodeURIComponent(vlogId)}`
        );

        if (!response.ok) {
            throw new Error("Failed to fetch vlog count");
        }

        return response.json();
    }
}
