import { AdminOtpRepository } from "../repositories/AdminOtpRepository.js";

export class AdminOtpService {
    constructor() {
        /** @type {import("../interfaces/IAdminOtpRepository.js").IAdminOtpRepository} */
        this.repository = new AdminOtpRepository();
    }

    async fetchEmail() {
        try {
            return await this.repository.fetchEmail();
        } catch (error) {
            console.error("AdminOtpService Error:", error);
            throw error;
        }
    }

    async saveEmail(email) {
        try {
            return await this.repository.saveEmail(email);
        } catch (error) {
            console.error("AdminOtpService Error:", error);
            throw error;
        }
    }

    async sendOtp() {
        try {
            return this.toPayload(await this.repository.sendOtp(), "Failed to send OTP.");
        } catch (error) {
            console.error("AdminOtpService Error:", error);
            throw error;
        }
    }

    async verifyOtp(otp) {
        try {
            return this.toPayload(await this.repository.verifyOtp(otp), "Failed to verify OTP.");
        } catch (error) {
            console.error("AdminOtpService Error:", error);
            throw error;
        }
    }

    async resetOtp() {
        try {
            return await this.repository.resetOtp();
        } catch (error) {
            console.error("AdminOtpService Error:", error);
            throw error;
        }
    }

    toPayload(result, fallback) {
        if (!result.ok || !result.data || result.data.ok !== true) {
            const message = (result.data && result.data.message) || fallback;
            const error = new Error(message);
            error.status = result.status;
            error.retry_after_seconds = result.data ? result.data.retry_after_seconds : undefined;
            error.attempts_remaining = result.data ? result.data.attempts_remaining : undefined;
            error.reason = result.data ? result.data.reason : undefined;
            throw error;
        }

        return result.data;
    }
}
