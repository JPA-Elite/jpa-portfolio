import { IAdminFaceRepository } from "../interfaces/IAdminFaceRepository.js";

export class AdminFaceRepository extends IAdminFaceRepository {
    constructor(baseUrl = "/admin/api/face") {
        super();
        this.baseUrl = baseUrl;
    }

    async post(path, frames) {
        const response = await fetch(`${this.baseUrl}/${path}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image_b64_list: frames }),
        });

        let data = null;
        try {
            data = await response.json();
        } catch (error) {
            data = null;
        }

        return { ok: response.ok, status: response.status, data };
    }

    async register(frames) {
        return this.post("register", frames);
    }

    async verify(frames) {
        return this.post("verify", frames);
    }
}
