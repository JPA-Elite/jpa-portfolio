// services/MusicService.js
import { MusicRepository } from "../repositories/MusicRepository.js";

export class MusicService {
    constructor() {
        /** @type {import("../interfaces/IMusicRepository.js").IMusicRepository} */
        this.repository = new MusicRepository();
    }

    async fetchMusicList(params) {
        try {
            return await this.repository.fetchMusicList(params);
        } catch (error) {
            console.error("MusicService Error:", error);
            throw error;
        }
    }

    async fetchCategories() {
        try {
            return await this.repository.fetchCategories();
        } catch (error) {
            console.error("MusicService Error:", error);
            throw error;
        }
    }
}
