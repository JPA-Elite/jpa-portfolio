from bson import ObjectId
from Repositories.Interfaces.IAuthRepository import IAuthRepository
from Repositories.BaseRepository import BaseRepository
from constants.db_collections import MongoCollections as mc

class AuthRepository(IAuthRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.USERS)  # use "users" collection

    def find_by_username(self, username: str):
        """Find user by username"""
        return self.collection.find_one({"username": username, "role": "admin"})

    def find_by_id(self, id):
        return self.collection.find_one({"_id": ObjectId(id)})

    def update_user(self, id, data: dict):
        return self.collection.update_one({"_id": ObjectId(id)}, {"$set": data})