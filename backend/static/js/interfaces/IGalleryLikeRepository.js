// interfaces/IGalleryLikeRepository.js

export class IGalleryLikeRepository {
    async toggleLike(galleryId) {
        throw new Error("Method 'toggleLike()' must be implemented.");
    }

    async fetchCountsBatch(galleryIds) {
        throw new Error("Method 'fetchCountsBatch()' must be implemented.");
    }

    async fetchCounts(galleryId) {
        throw new Error("Method 'fetchCounts()' must be implemented.");
    }
}
