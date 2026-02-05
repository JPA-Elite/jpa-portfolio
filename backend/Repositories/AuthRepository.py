from bson import ObjectId
from backend.Repositories.Interfaces.IAuthRepository import IAuthRepository
from backend.Repositories.BaseRepository import BaseRepository
from backend.constants.db_collections import MongoCollections as mc

class AuthRepository(IAuthRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.USERS)  # use "users" collection

    def find_by_username(self, username: str):
        """Find user by username"""
        return self.get_document({"username": username, "role": "admin"})

    def find_by_id(self, id):
        return self.get_document({"_id": ObjectId(id)})

    def update_user(self, id, data: dict):
        return self.update_document_by_id(ObjectId(id), data)