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

    async streamMessage(message, sessionId, onToken, signal) {
        const response = await fetch(`${this.baseUrl}/chat/stream`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            body: JSON.stringify({ message, session_id: sessionId }),
            signal,
        });

        if (!response.ok || !response.body || typeof response.body.getReader !== "function") {
            return this.sendMessage(message, sessionId);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let result = null;

        const consume = (block) => {
            for (const line of block.split("\n")) {
                if (!line.startsWith("data:")) continue;
                const payload = line.slice(5).trim();
                if (!payload || payload === "[DONE]") continue;
                let event;
                try {
                    event = JSON.parse(payload);
                } catch {
                    continue;
                }
                if (event.type === "token" && typeof event.text === "string") {
                    if (event.text && typeof onToken === "function") onToken(event.text);
                } else if (event.type === "final") {
                    result = event.result || null;
                }
            }
        };

        try {
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                let index = buffer.indexOf("\n\n");
                while (index !== -1) {
                    consume(buffer.slice(0, index));
                    buffer = buffer.slice(index + 2);
                    index = buffer.indexOf("\n\n");
                }
            }
            buffer += decoder.decode();
            if (buffer.trim()) consume(buffer);
        } catch (error) {
            console.error("Chat stream error:", error);
        } finally {
            try {
                reader.releaseLock();
            } catch {}
        }

        return result;
    }
}
