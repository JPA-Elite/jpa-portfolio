export class ICommentRepository {
    async fetchComments(params) {
        throw new Error("Method 'fetchComments()' must be implemented.");
    }

    async createComment(params) {
        throw new Error("Method 'createComment()' must be implemented.");
    }

    async deleteComment(basePath, commentId) {
        throw new Error("Method 'deleteComment()' must be implemented.");
    }

    async deleteAllComments(params) {
        throw new Error("Method 'deleteAllComments()' must be implemented.");
    }

    async toggleCommentLike(basePath, commentId) {
        throw new Error("Method 'toggleCommentLike()' must be implemented.");
    }

    async fetchAvatar() {
        throw new Error("Method 'fetchAvatar()' must be implemented.");
    }

    async saveAvatar(avatarUrl) {
        throw new Error("Method 'saveAvatar()' must be implemented.");
    }

    async uploadAvatar(formData) {
        throw new Error("Method 'uploadAvatar()' must be implemented.");
    }

    async removeAvatar() {
        throw new Error("Method 'removeAvatar()' must be implemented.");
    }

    async fetchUsername() {
        throw new Error("Method 'fetchUsername()' must be implemented.");
    }

    async saveUsername(displayName) {
        throw new Error("Method 'saveUsername()' must be implemented.");
    }
}
