import { IChatRepository } from "../interfaces/IChatRepository.js";

export class ChatRepository extends IChatRepository {
    constructor(baseUrl = "/api") {
        super();
        this.baseUrl = baseUrl;
    }

    async fetchProfileConfig() {
        const response = await fetch(`${this.baseUrl}/profile-config`, {
            cache: "no-store",
        });

        if (!response.ok) {
            throw new Error("Failed to load profile config");
        }

        return response.json();
    }

    async sendMessage(message, sessionId) {
        const response = await fetch(`${this.baseUrl}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, session_id: sessionId }),
        });

        if (!response.ok) {
            return null;
        }

        return response.json();
    }
}
