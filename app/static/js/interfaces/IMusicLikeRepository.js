export class IMusicLikeRepository {
    async fetchCountsBatch(musicIds) {
        throw new Error("Method 'fetchCountsBatch()' must be implemented.");
    }

    async toggleVote(musicId, isLike) {
        throw new Error("Method 'toggleVote()' must be implemented.");
    }

    async fetchCounts(musicId) {
        throw new Error("Method 'fetchCounts()' must be implemented.");
    }
}
