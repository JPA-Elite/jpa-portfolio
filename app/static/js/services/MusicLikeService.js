import { MusicLikeRepository } from "../repositories/MusicLikeRepository.js";

export class MusicLikeService {
    constructor() {
        /** @type {import("../interfaces/IMusicLikeRepository.js").IMusicLikeRepository} */
        this.repository = new MusicLikeRepository();
    }

    async fetchCountsBatch(musicIds) {
        try {
            return await this.repository.fetchCountsBatch(musicIds);
        } catch (error) {
            console.error("MusicLikeService Error:", error);
            throw error;
        }
    }

    async toggleVote(musicId, isLike) {
        try {
            return await this.repository.toggleVote(musicId, isLike);
        } catch (error) {
            console.error("MusicLikeService Error:", error);
            throw error;
        }
    }

    async fetchCounts(musicId) {
        try {
            return await this.repository.fetchCounts(musicId);
        } catch (error) {
            console.error("MusicLikeService Error:", error);
            throw error;
        }
    }
}
