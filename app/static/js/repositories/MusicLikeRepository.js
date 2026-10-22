import { IMusicLikeRepository } from "../interfaces/IMusicLikeRepository.js";

export class MusicLikeRepository extends IMusicLikeRepository {
    constructor(baseUrl = "/api/music-like") {
        super();
        this.baseUrl = baseUrl;
    }

    async fetchCountsBatch(musicIds) {
        const ids = Array.isArray(musicIds) ? musicIds.join(",") : String(musicIds || "");
        const params = new URLSearchParams({ music_ids: ids });
        const response = await fetch(`${this.baseUrl}/counts/batch?${params.toString()}`);

        if (!response.ok) {
            throw new Error("Failed to fetch music like counts");
        }

        return response.json();
    }

    async toggleVote(musicId, isLike) {
        const response = await fetch(`${this.baseUrl}/vote`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ music_id: musicId, is_like: Boolean(isLike) }),
        });

        if (!response.ok) {
            throw new Error("Failed to toggle music vote");
        }

        return response.json();
    }

    async fetchCounts(musicId) {
        const params = new URLSearchParams({ music_id: musicId });
        const response = await fetch(`${this.baseUrl}/counts?${params.toString()}`);

        if (!response.ok) {
            throw new Error("Failed to fetch music like counts");
        }

        return response.json();
    }
}
