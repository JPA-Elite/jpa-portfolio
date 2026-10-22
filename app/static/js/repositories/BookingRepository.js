import { IBookingRepository } from "../interfaces/IBookingRepository.js";

export class BookingRepository extends IBookingRepository {
    constructor(baseUrl = "/api/booking") {
        super();
        this.baseUrl = baseUrl;
    }

    async send(payload) {
        const response = await fetch(`${this.baseUrl}/send`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        let data = null;
        try {
            data = await response.json();
        } catch (error) {
            data = null;
        }

        return { status: response.status, data };
    }
}
