import { IBuiltAppLikeRepository } from "../interfaces/IBuiltAppLikeRepository.js";

export class BuiltAppLikeRepository extends IBuiltAppLikeRepository {
    constructor(baseUrl = "/api/built-app-like") {
        super();
        this.baseUrl = baseUrl;
    }

    async fetchCounts(appId) {
        const params = new URLSearchParams({ app_id: appId });
        const response = await fetch(`${this.baseUrl}/counts?${params.toString()}`);

        if (!response.ok) {
            throw new Error("Failed to fetch built app like counts");
        }

        return response.json();
    }

    async vote(appId, isLike) {
        const response = await fetch(`${this.baseUrl}/vote`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ app_id: appId, is_like: Boolean(isLike) }),
        });

        if (!response.ok) {
            throw new Error("Failed to submit built app vote");
        }

        return response.json();
    }
}
