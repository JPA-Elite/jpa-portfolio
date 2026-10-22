import { BookingRepository } from "../repositories/BookingRepository.js";

export class BookingService {
    constructor() {
        /** @type {import("../interfaces/IBookingRepository.js").IBookingRepository} */
        this.repository = new BookingRepository();
    }

    async send(payload) {
        try {
            return await this.repository.send(payload);
        } catch (error) {
            console.error("BookingService Error:", error);
            throw error;
        }
    }
}
