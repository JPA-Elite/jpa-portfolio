from bson import ObjectId
from app.Repositories.Interfaces.IAuthRepository import IAuthRepository
from app.Repositories.BaseRepository import BaseRepository
from app.constants.db_collections import MongoCollections as mc

class AuthRepository(IAuthRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.USERS)

    def find_by_username(self, username: str):
        return self.find_one({"username": username, "role": "admin"})

    def find_by_id(self, id):
        return self.find_one({"_id": ObjectId(id)})

    def update_user(self, id, data: dict):
        return self.update_one({"_id": ObjectId(id)}, {"$set": data})

    def get_face_records(self, id):
        return self.find_one({"_id": ObjectId(id)}) or {}

    def update_face_reference(self, id, face_crop_b64: str, registered_at: str):
        result = self.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "face_reference_crop_b64": face_crop_b64,
                    "face_reference_hash": "",
                    "face_last_registered_at": registered_at,
                }
            },
            upsert=False,
        )
        return result.matched_count > 0

    def update_face_verified(self, id, verified_at: str, distance: float):
        result = self.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "face_last_verified_at": verified_at,
                    "face_last_verify_distance": distance,
                }
            },
            upsert=False,
        )
        return result.matched_count > 0

    def get_user_email(self, id):
        user_doc = self.find_by_id(id) or {}
        return (user_doc.get("email") or "").strip()
