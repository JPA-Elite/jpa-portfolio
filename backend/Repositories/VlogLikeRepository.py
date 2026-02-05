from backend.Repositories.Interfaces.IVlogLikeRepository import IVlogLikeRepository
from backend.Repositories.BaseRepository import BaseRepository
from backend.constants.db_collections import MongoCollections as mc
from backend.Models.VlogLike import VlogLike
class VlogLikeRepository(IVlogLikeRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VIDEO_LIKES)  # use "vlog" collection

    def get_vlog_likes_count_by_id(self, vlog_id: str):
        """Return total number of likes for a specific vlog item."""
        count = self.count({
            "vlog_id": vlog_id,
            "like": True
        })
        return count


    def get_vlog_likes_by_id_and_ip(self, vlog_id: str, ip_address: str, fields: dict = None):
        projection = fields or None

        # Normalize incoming IP list
        input_ips = [ip.strip() for ip in ip_address.replace(",", " ").split() if ip.strip()]
        if not input_ips:
            return None

        # Build regex patterns that match any of the given IPs
        regex_conditions = [
            {
                "vlog_id": vlog_id,
                "ip_address": {
                    "$regex": fr"(^|[,\s]+){ip}([,\s]+|$)",
                    "$options": "i"
                }
            }
            for ip in input_ips
        ]

        # Combine with $or for MongoDB to check any match
        query = {"$or": regex_conditions}

        # This will let MongoDB handle filtering efficiently
        return self.get_document(query, projection)


    def add_vlog_like(self, vlog_like: VlogLike):
        """Insert a new vlog document into MongoDB."""
        result = self.insert_document(vlog_like.to_dict())
        return str(result.inserted_id)

    def update_vlog_like(self, vlog_like: VlogLike):
        """
        Update a vlog like document by its vlog_id and ip_address.
        This is safer since we identify likes by (vlog_id + ip_address).
        """
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



