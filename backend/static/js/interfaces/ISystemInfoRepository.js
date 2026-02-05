// interfaces/ISystemInfoRepository.js

export class ISystemInfoRepository {
    /**
     * Delete records from system info endpoint.
     * @param {Array<{_id?: string, image_capture?: string | null}>} records
     * @returns {Promise<{status?: string, message?: string}>}
     */
    async deletePageSystemInfo(records) {
        throw new Error("Method 'deletePageSystemInfo(records)' must be implemented.");
    }
}
