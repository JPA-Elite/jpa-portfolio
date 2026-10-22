export class IChatRepository {
    async fetchProfileConfig() {
        throw new Error("Method 'fetchProfileConfig()' must be implemented.");
    }

    async sendMessage(message, sessionId) {
        throw new Error("Method 'sendMessage()' must be implemented.");
    }
}
