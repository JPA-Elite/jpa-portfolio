from app.Repositories.Interfaces.IGalleryLikeRepository import IGalleryLikeRepository
from app.Repositories.BaseRepository import BaseRepository
from app.constants.db_collections import MongoCollections as mc
from app.Models.GalleryLike import GalleryLike
class GalleryLikeRepository(IGalleryLikeRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.GALLERY_LIKES)

    def get_gallery_likes_count_by_id(self, gallery_id: str):
        count = self.collection.count_documents({
            "gallery_id": gallery_id,
            "like": True
        })
        return count

    def get_gallery_likes_by_id_and_ip(self, gallery_id: str, ip_address: str, fields: dict = None):
        projection = fields or None

        input_ips = [ip.strip() for ip in ip_address.replace(",", " ").split() if ip.strip()]
        if not input_ips:
            return None

        regex_conditions = [
            {
                "gallery_id": gallery_id,
                "ip_address": {
                    "$regex": fr"(^|[,\s]+){ip}([,\s]+|$)",
                    "$options": "i"
                }
            }
            for ip in input_ips
        ]

        query = {"$or": regex_conditions}

        return self.collection.find_one(query, projection)

    def add_gallery_like(self, gallery_like: GalleryLike):
        result = self.collection.insert_one(gallery_like.to_dict())
        return str(result.inserted_id)

    def update_gallery_like(self, gallery_like: GalleryLike):
        result = self.collection.update_one(
            {
                "gallery_id": gallery_like.gallery_id,
                "ip_address": gallery_like.ip_address
            },
            {
                "$set": {
                    "like": gallery_like.like
                }
            }
        )
        return result.modified_count > 0

