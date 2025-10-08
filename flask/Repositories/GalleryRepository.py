from Repositories.Interfaces.IGalleryRepository import IGalleryRepository
from Repositories.BaseRepository import BaseRepository
from config import SortOrder
from constants.db_collections import MongoCollections as mc
from bson import ObjectId
from Models.Gallery import Gallery

class GalleryRepository(IGalleryRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.GALLERY)  # use "gallery" collection

    def get_gallery_by_id(self, gallery_id: str):
        """Fetch a gallery document by _id."""
        return self.collection.find_one({"_id": ObjectId(gallery_id)})

    def get_paginated_gallery_list(self, page: int, per_page: int, order: SortOrder):
        # Mongo sort order by _id
        sort_order = -1 if order == SortOrder.DESC else 1

        # Use MongoDB skip + limit for pagination
        cursor = (
            self.collection.find()
            .sort("_id", sort_order)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )

        data = list(cursor)
        total_data = self.collection.count_documents({})

        return data, total_data

    def add_gallery(self, gallery: Gallery):
        """Insert a new gallery document into MongoDB."""
        result = self.collection.insert_one(gallery.to_dict())
        return str(result.inserted_id)

    def update_gallery(self, gallery_id: str, gallery: Gallery):
        """Update a gallery document by _id."""
        result = self.collection.update_one(
            {"_id": ObjectId(gallery_id)},
            {"$set": gallery.to_dict()}
        )
        return result.matched_count > 0  # True if updated

    def delete_gallery(self, gallery_id: str):
        """Delete a gallery document by _id."""
        result = self.collection.delete_one({"_id": ObjectId(gallery_id)})
        return result.deleted_count > 0  # True if deleted
