// services/VlogLikeService.js
import { VlogLikeRepository } from "../repositories/VlogLikeRepository.js";

export class VlogLikeService {
    constructor() {
        /** @type {import("../interfaces/IVlogLikeRepository.js").IVlogLikeRepository} */
        this.repository = new VlogLikeRepository();
    }

    async toggleLike(vlogId) {
        try {
            return await this.repository.toggleLike(vlogId);
        } catch (error) {
            console.error("VlogLikeService Error:", error);
            throw error;
        }
    }

    async fetchCountsBatch(vlogIds) {
        try {
            return await this.repository.fetchCountsBatch(vlogIds);
        } catch (error) {
            console.error("VlogLikeService Error:", error);
            throw error;
        }
    }

    async fetchCounts(vlogId) {
        try {
            return await this.repository.fetchCounts(vlogId);
        } catch (error) {
            console.error("VlogLikeService Error:", error);
            throw error;
        }
    }
}
