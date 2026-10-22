import { IAdminOtpRepository } from "../interfaces/IAdminOtpRepository.js";

export class AdminOtpRepository extends IAdminOtpRepository {
    constructor(baseUrl = "/admin/api/otp") {
        super();
        this.baseUrl = baseUrl;
    }

    async request(path, options) {
        const response = await fetch(`${this.baseUrl}${path}`, options);
        let data = null;
        try {
            data = await response.json();
        } catch (error) {
            data = null;
        }
        return { ok: response.ok, status: response.status, data };
    }

    async fetchEmail() {
        return this.request("/email", { method: "GET" });
    }

    async saveEmail(email) {
        return this.request("/email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });
    }

    async sendOtp() {
        return this.request("/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({}),
        });
    }

    async verifyOtp(otp) {
        return this.request("/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ otp }),
        });
    }

    async resetOtp() {
        return this.request("/reset", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({}),
        });
    }
}
