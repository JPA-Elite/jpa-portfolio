import re
from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.Interfaces.IMusicLikeRepository import IMusicLikeRepository
from app.constants.db_collections import MongoCollections as mc
from app.Models.MusicLike import MusicLike

class MusicLikeRepository(IMusicLikeRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.MUSIC_LIKES)

    def get_likes_count(self, music_id: str, is_like: bool = True):
        return self.count_documents({"music_id": music_id, "is_like": is_like})

    def get_dislikes_count(self, music_id: str):
        return self.get_likes_count(music_id, is_like=False)

    def get_likes_counts_by_ids(self, music_ids: list[str], is_like: bool = True):
        if not music_ids:
            return {}

        pipeline = [
            {
                "$match": {
                    "music_id": {"$in": music_ids},
                    "is_like": is_like,
                }
            },
            {
                "$group": {
                    "_id": "$music_id",
                    "count": {"$sum": 1},
                }
            },
        ]

        return {
            str(item["_id"]): int(item.get("count", 0))
            for item in self.aggregate(pipeline)
        }

    def get_user_vote(self, music_id: str, ip_address: str):
        if not ip_address:
            return None

        input_ips = [ip.strip() for ip in ip_address.replace(",", " ").split() if ip.strip()]
        if not input_ips:
            return None

        regex_conditions = [
            {
                "music_id": music_id,
                "ip_address": {
                    "$regex": fr"(^|[,\s]+){re.escape(ip)}([,\s]+|$)",
                    "$options": "i",
                },
            }
            for ip in input_ips
        ]

        return self.find_one({"$or": regex_conditions})

    def add_vote(self, vote: MusicLike):
        result = self.insert_one(vote.to_dict())
        return str(result.inserted_id)

    def update_vote(self, vote: MusicLike):
        result = self.update_one(
            {"music_id": vote.music_id, "ip_address": vote.ip_address},
            {"$set": {"is_like": vote.is_like}},
        )
        return result.modified_count > 0

    def delete_vote(self, music_id: str, ip_address: str):
        result = self.delete_one({"music_id": music_id, "ip_address": ip_address})
        return result.deleted_count > 0
