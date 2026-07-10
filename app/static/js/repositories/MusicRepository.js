// repositories/MusicRepository.js
import { IMusicRepository } from "../interfaces/IMusicRepository.js";

export class MusicRepository extends IMusicRepository {
    constructor(baseUrl = "/api/music-list") {
        super();
        this.baseUrl = baseUrl;
    }

    async fetchMusicList(params) {
        const query =
            params instanceof URLSearchParams
                ? params.toString()
                : new URLSearchParams(params || {}).toString();

        const response = await fetch(`${this.baseUrl}?${query}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch music list: ${response.status}`);
        }

        return response.json();
    }

    async fetchCategories() {
        const response = await fetch("/api/music-categories");
        if (!response.ok) {
            throw new Error(`Failed to fetch categories: ${response.status}`);
        }
        return response.json();
    }
}
