// interfaces/IVlogLikeRepository.js

export class IVlogLikeRepository {
    async toggleLike(vlogId) {
        throw new Error("Method 'toggleLike()' must be implemented.");
    }

    async fetchCountsBatch(vlogIds) {
        throw new Error("Method 'fetchCountsBatch()' must be implemented.");
    }

    async fetchCounts(vlogId) {
        throw new Error("Method 'fetchCounts()' must be implemented.");
    }
}
