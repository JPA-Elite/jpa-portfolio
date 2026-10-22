export class IAdminOtpRepository {
    async fetchEmail() {
        throw new Error("Method 'fetchEmail()' must be implemented.");
    }

    async saveEmail(email) {
        throw new Error("Method 'saveEmail()' must be implemented.");
    }

    async sendOtp() {
        throw new Error("Method 'sendOtp()' must be implemented.");
    }

    async verifyOtp(otp) {
        throw new Error("Method 'verifyOtp()' must be implemented.");
    }

    async resetOtp() {
        throw new Error("Method 'resetOtp()' must be implemented.");
    }
}
