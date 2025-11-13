from backend.Repositories.Interfaces.IGalleryLikeRepository import IGalleryLikeRepository
from backend.Repositories.BaseRepository import BaseRepository
from backend.configurations import SortOrder
from backend.constants.db_collections import MongoCollections as mc
from bson import ObjectId
from backend.Models.GalleryLike import GalleryLike
from bson.regex import Regex
class GalleryLikeRepository(IGalleryLikeRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.GALLERY_LIKES)  # use "gallery" collection

    def get_gallery_likes_count_by_id(self, gallery_id: str):
        """Return total number of likes for a specific gallery item."""
        count = self.collection.count_documents({
            "gallery_id": gallery_id,
            "like": True
        })
        return count

    def get_gallery_likes_by_id_and_ip(self, gallery_id: str, ip_address: str, fields: dict = None):
        """
        Check if a specific IP has already liked a specific gallery item.
        Optionally limit which fields to return using the 'fields' (projection) parameter.

        Example:
            repo.get_gallery_likes_by_id_and_ip("123", "192.168.0.1", {"_id": 1, "like": 1})
        """
        query = {
            "gallery_id": gallery_id,
            "ip_address": ip_address
        }

        # Apply projection if provided
        if fields:
            return self.collection.find_one(query, fields)
        else:
            return self.collection.find_one(query)


    def add_gallery_like(self, gallery_like: GalleryLike):
        """Insert a new gallery document into MongoDB."""
        result = self.collection.insert_one(gallery_like.to_dict())
        return str(result.inserted_id)

    def update_gallery_like(self, gallery_like: GalleryLike):
        """
        Update a gallery like document by its gallery_id and ip_address.
        This is safer since we identify likes by (gallery_id + ip_address).
        """
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



