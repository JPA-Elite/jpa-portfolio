// services/GalleryLikeService.js
import { GalleryLikeRepository } from "../repositories/GalleryLikeRepository.js";

export class GalleryLikeService {
    constructor() {
        /** @type {import("../interfaces/IGalleryLikeRepository.js").IGalleryLikeRepository} */
        this.repository = new GalleryLikeRepository();
    }

    async toggleLike(galleryId) {
        try {
            return await this.repository.toggleLike(galleryId);
        } catch (error) {
            console.error("GalleryLikeService Error:", error);
            throw error;
        }
    }

    async fetchCountsBatch(galleryIds) {
        try {
            return await this.repository.fetchCountsBatch(galleryIds);
        } catch (error) {
            console.error("GalleryLikeService Error:", error);
            throw error;
        }
    }

    async fetchCounts(galleryId) {
        try {
            return await this.repository.fetchCounts(galleryId);
        } catch (error) {
            console.error("GalleryLikeService Error:", error);
            throw error;
        }
    }
}
