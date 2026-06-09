import re
from backend.Repositories.Interfaces.IVlogLikeRepository import IVlogLikeRepository
from backend.Repositories.BaseRepository import BaseRepository
from backend.constants.db_collections import MongoCollections as mc
from backend.Models.VlogLike import VlogLike

class VlogLikeRepository(IVlogLikeRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VIDEO_LIKES)

    def get_vlog_likes_count_by_id(self, vlog_id: str):
        count = self.collection.count_documents({
            "vlog_id": vlog_id,
            "like": True
        })
        return count

    def get_vlog_likes_counts_by_ids(self, vlog_ids: list[str]):
        if not vlog_ids:
            return {}

        pipeline = [
            {
                "$match": {
                    "vlog_id": {"$in": vlog_ids},
                    "like": True
                }
            },
            {
                "$group": {
                    "_id": "$vlog_id",
                    "count": {"$sum": 1}
                }
            }
        ]

        return {
            str(item["_id"]): int(item.get("count", 0))
            for item in self.collection.aggregate(pipeline)
        }

    def get_vlog_liked_states_by_ids_and_ip(self, vlog_ids: list[str], ip_address: str):
        if not vlog_ids:
            return {}

        regex_conditions = self._build_ip_regex_conditions(ip_address, vlog_ids=vlog_ids)
        if not regex_conditions:
            return {}

        pipeline = [
            {
                "$match": {
                    "$or": regex_conditions
                }
            },
            {
                "$group": {
                    "_id": "$vlog_id",
                    "is_liked": {
                        "$max": {
                            "$cond": ["$like", 1, 0]
                        }
                    }
                }
            }
        ]

        return {
            str(item["_id"]): bool(item.get("is_liked"))
            for item in self.collection.aggregate(pipeline)
        }

    def get_vlog_likes_by_id_and_ip(self, vlog_id: str, ip_address: str, fields: dict = None):
        projection = fields or None

        regex_conditions = self._build_ip_regex_conditions(ip_address, vlog_id=vlog_id)
        if not regex_conditions:
            return None

        query = {"$or": regex_conditions}

        return self.collection.find_one(query, projection)

    def _build_ip_regex_conditions(self, ip_address: str, vlog_id: str = None, vlog_ids: list[str] = None):
        if not ip_address:
            return []

        input_ips = [ip.strip() for ip in ip_address.replace(",", " ").split() if ip.strip()]
        if not input_ips:
            return []

        conditions = []
        for ip in input_ips:
            escaped_ip = re.escape(ip)
            base_condition = {
                "ip_address": {
                    "$regex": fr"(^|[,\s]+){escaped_ip}([,\s]+|$)",
                    "$options": "i"
                }
            }

            if vlog_id is not None:
                base_condition["vlog_id"] = vlog_id
            elif vlog_ids is not None:
                base_condition["vlog_id"] = {"$in": vlog_ids}

            conditions.append(base_condition)

        return conditions

    def add_vlog_like(self, vlog_like: VlogLike):
        result = self.collection.insert_one(vlog_like.to_dict())
        return str(result.inserted_id)

    def update_vlog_like(self, vlog_like: VlogLike):
        result = self.collection.update_one(
            {
                "vlog_id": vlog_like.vlog_id,
                "ip_address": vlog_like.ip_address
            },
            {
                "$set": {
                    "like": vlog_like.like
                }
            }
        )
        return result.modified_count > 0

