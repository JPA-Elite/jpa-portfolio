import re
from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.Interfaces.IBuiltAppLikeRepository import IBuiltAppLikeRepository
from app.constants.db_collections import MongoCollections as mc
from app.Models.BuiltAppLike import BuiltAppLike

class BuiltAppLikeRepository(IBuiltAppLikeRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.BUILT_APP_LIKES)

    def get_likes_count(self, app_id: str, is_like: bool = True):
        return self.count_documents({"app_id": app_id, "is_like": is_like})

    def get_dislikes_count(self, app_id: str):
        return self.get_likes_count(app_id, is_like=False)

    def get_user_vote(self, app_id: str, ip_address: str):
        if not ip_address:
            return None

        input_ips = [ip.strip() for ip in ip_address.replace(",", " ").split() if ip.strip()]
        if not input_ips:
            return None

        regex_conditions = [
            {
                "app_id": app_id,
                "ip_address": {
                    "$regex": fr"(^|[,\s]+){re.escape(ip)}([,\s]+|$)",
                    "$options": "i",
                },
            }
            for ip in input_ips
        ]

        return self.find_one({"$or": regex_conditions})

    def add_vote(self, vote: BuiltAppLike):
        result = self.insert_one(vote.to_dict())
        return str(result.inserted_id)

    def update_vote(self, vote: BuiltAppLike):
        result = self.update_one(
            {"app_id": vote.app_id, "ip_address": vote.ip_address},
            {"$set": {"is_like": vote.is_like}},
        )
        return result.modified_count > 0

    def delete_vote(self, app_id: str, ip_address: str):
        result = self.delete_one({"app_id": app_id, "ip_address": ip_address})
        return result.deleted_count > 0
