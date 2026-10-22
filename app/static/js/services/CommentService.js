import { CommentRepository } from "../repositories/CommentRepository.js";

export class CommentService {
    constructor() {
        /** @type {import("../interfaces/ICommentRepository.js").ICommentRepository} */
        this.repository = new CommentRepository();
    }

    async fetchComments(params) {
        try {
            return await this.repository.fetchComments(params);
        } catch (error) {
            console.error("CommentService Error:", error);
            throw error;
        }
    }

    async createComment(params) {
        try {
            return await this.repository.createComment(params);
        } catch (error) {
            console.error("CommentService Error:", error);
            throw error;
        }
    }

    async deleteComment(basePath, commentId) {
        try {
            return await this.repository.deleteComment(basePath, commentId);
        } catch (error) {
            console.error("CommentService Error:", error);
            throw error;
        }
    }

    async deleteAllComments(params) {
        try {
            return await this.repository.deleteAllComments(params);
        } catch (error) {
            console.error("CommentService Error:", error);
            throw error;
        }
    }

    async toggleCommentLike(basePath, commentId) {
        try {
            return await this.repository.toggleCommentLike(basePath, commentId);
        } catch (error) {
            console.error("CommentService Error:", error);
            throw error;
        }
    }

    async fetchAvatar() {
        try {
            return await this.repository.fetchAvatar();
        } catch (error) {
            console.error("CommentService Error:", error);
            throw error;
        }
    }

    async saveAvatar(avatarUrl) {
        try {
            return await this.repository.saveAvatar(avatarUrl);
        } catch (error) {
            console.error("CommentService Error:", error);
            throw error;
        }
    }

    async uploadAvatar(formData) {
        try {
            return await this.repository.uploadAvatar(formData);
        } catch (error) {
            console.error("CommentService Error:", error);
            throw error;
        }
    }

    async removeAvatar() {
        try {
            return await this.repository.removeAvatar();
        } catch (error) {
            console.error("CommentService Error:", error);
            throw error;
        }
    }

    async fetchUsername() {
        try {
            return await this.repository.fetchUsername();
        } catch (error) {
            console.error("CommentService Error:", error);
            throw error;
        }
    }

    async saveUsername(displayName) {
        try {
            return await this.repository.saveUsername(displayName);
        } catch (error) {
            console.error("CommentService Error:", error);
            throw error;
        }
    }
}
