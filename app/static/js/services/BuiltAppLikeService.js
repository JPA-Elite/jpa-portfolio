import { BuiltAppLikeRepository } from "../repositories/BuiltAppLikeRepository.js";

export class BuiltAppLikeService {
    constructor() {
        /** @type {import("../interfaces/IBuiltAppLikeRepository.js").IBuiltAppLikeRepository} */
        this.repository = new BuiltAppLikeRepository();
    }

    async fetchCounts(appId) {
        try {
            return await this.repository.fetchCounts(appId);
        } catch (error) {
            console.error("BuiltAppLikeService Error:", error);
            throw error;
        }
    }

    async vote(appId, isLike) {
        try {
            return await this.repository.vote(appId, isLike);
        } catch (error) {
            console.error("BuiltAppLikeService Error:", error);
            throw error;
        }
    }
}
