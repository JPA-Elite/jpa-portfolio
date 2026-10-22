import { ICommentRepository } from "../interfaces/ICommentRepository.js";

export class CommentRepository extends ICommentRepository {
    constructor(baseUrl = "/api") {
        super();
        this.baseUrl = baseUrl;
    }

    async request(url, options) {
        const response = await fetch(url, options);
        let data = null;
        try {
            data = await response.json();
        } catch (error) {
            data = null;
        }
        return { ok: response.ok, status: response.status, data };
    }

    async fetchComments({ basePath, idType, id, page, limit }) {
        const params = new URLSearchParams({
            [idType]: id,
            page,
            limit,
        });
        return this.request(`${this.baseUrl}/${basePath}?${params.toString()}`);
    }

    async createComment({ basePath, idType, id, authorName, text }) {
        const body = {
            author_name: authorName,
            text,
        };
        body[idType] = id;

        return this.request(`${this.baseUrl}/${basePath}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
    }

    async deleteComment(basePath, commentId) {
        return this.request(`${this.baseUrl}/${basePath}/${commentId}`, {
            method: "DELETE",
        });
    }

    async deleteAllComments({ basePath, idType, id }) {
        const body = {};
        body[idType] = id;

        return this.request(`${this.baseUrl}/${basePath}/delete-all`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
    }

    async toggleCommentLike(basePath, commentId) {
        return this.request(`${this.baseUrl}/${basePath}/like`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ comment_id: commentId }),
        });
    }

    async fetchAvatar() {
        return this.request(`${this.baseUrl}/comment-avatar`, { method: "GET" });
    }

    async saveAvatar(avatarUrl) {
        return this.request(`${this.baseUrl}/comment-avatar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ avatar_url: avatarUrl }),
        });
    }

    async uploadAvatar(formData) {
        return this.request(`${this.baseUrl}/comment-avatar/upload`, {
            method: "POST",
            body: formData,
        });
    }

    async removeAvatar() {
        return this.request(`${this.baseUrl}/comment-avatar`, { method: "DELETE" });
    }

    async fetchUsername() {
        return this.request(`${this.baseUrl}/comment-username`, { method: "GET" });
    }

    async saveUsername(displayName) {
        return this.request(`${this.baseUrl}/comment-username`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ display_name: displayName }),
        });
    }
}
