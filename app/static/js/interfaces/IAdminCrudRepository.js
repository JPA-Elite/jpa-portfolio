// interfaces/IAdminCrudRepository.js

export class IAdminCrudRepository {
    async fetchList(options) {
        throw new Error("Method 'fetchList()' must be implemented.");
    }

    async add(formData) {
        throw new Error("Method 'add()' must be implemented.");
    }

    async update(id, formData) {
        throw new Error("Method 'update()' must be implemented.");
    }

    async remove(id) {
        throw new Error("Method 'remove()' must be implemented.");
    }
}
