import { ChatRepository } from "../repositories/ChatRepository.js";

export class ChatService {
    constructor() {
        /** @type {import("../interfaces/IChatRepository.js").IChatRepository} */
        this.repository = new ChatRepository();
    }

    async fetchProfileConfig() {
        try {
            return await this.repository.fetchProfileConfig();
        } catch (error) {
            console.error("ChatService Error:", error);
            throw error;
        }
    }

    async sendMessage(message, sessionId) {
        try {
            return await this.repository.sendMessage(message, sessionId);
        } catch (error) {
            console.error("ChatService Error:", error);
            throw error;
        }
    }
}
