// interfaces/IAdminLoginAttemptsRepository.js

export class IAdminLoginAttemptsRepository {
    async fetchClientIp() {
        throw new Error("Method 'fetchClientIp()' must be implemented.");
    }

    async fetchList(options) {
        throw new Error("Method 'fetchList()' must be implemented.");
    }

    async remove(id) {
        throw new Error("Method 'remove()' must be implemented.");
    }
}
