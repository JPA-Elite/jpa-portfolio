export class IBuiltAppLikeRepository {
    async fetchCounts(appId) {
        throw new Error("Method 'fetchCounts()' must be implemented.");
    }

    async vote(appId, isLike) {
        throw new Error("Method 'vote()' must be implemented.");
    }
}
