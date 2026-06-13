// repositories/GalleryLikeRepository.js
import { IGalleryLikeRepository } from "../interfaces/IGalleryLikeRepository.js";

export class GalleryLikeRepository extends IGalleryLikeRepository {
    constructor(baseUrl = "/api/gallery-like") {
        super();
        this.baseUrl = baseUrl;
    }

    async toggleLike(galleryId) {
        const formData = new FormData();
        formData.append("gallery_id", JSON.stringify(galleryId));

        const response = await fetch(this.baseUrl, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error("Failed to toggle gallery like");
        }

        return response.json();
    }

    async fetchCountsBatch(galleryIds) {
        const params = new URLSearchParams();
        params.set("gallery_ids", galleryIds.join(","));

        const response = await fetch(
            `${this.baseUrl}/counts/batch?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error("Failed to fetch gallery counts");
        }

        return response.json();
    }

    async fetchCounts(galleryId) {
        const response = await fetch(
            `${this.baseUrl}/counts?gallery_id=${encodeURIComponent(galleryId)}`
        );

        if (!response.ok) {
            throw new Error("Failed to fetch gallery count");
        }

        return response.json();
    }
}
