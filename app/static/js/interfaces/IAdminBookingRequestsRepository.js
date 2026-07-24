export class IAdminBookingRequestsRepository {
    async fetchList(options) {
        throw new Error("Method 'fetchList()' must be implemented.");
    }

    async remove(id) {
        throw new Error("Method 'remove()' must be implemented.");
    }
}
