from Repositories.Interfaces.IGalleryRepository import IGalleryRepository
from Repositories.BaseRepository import BaseRepository
from config import SortOrder
from constants.db_collections import MongoCollections as mc
from bson import ObjectId
from Models.Gallery import Gallery
from bson.regex import Regex
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

    def search_gallery_paginated(
        self,
        search_query: str = "",
        tags=None,
        locale: str = "en",
        page: int = 1,
        per_page: int = 10,
        order: SortOrder = SortOrder.DESC
    ):
        query = {}

        # --- Handle tags: accept str (like "smile.invitation") or list ---
        if tags:
            if isinstance(tags, str):
                tags = tags.split('.')  # convert 'smile.invitation' → ['smile', 'invitation']
            elif not isinstance(tags, list):
                tags = [tags]  # wrap single tag
            query["tags"] = {"$in": tags}

        # --- Build search filter ---
        if search_query:
            search_regex = Regex(search_query, "i")
            query["$or"] = [
                {f"title.{locale}": search_regex},
                {f"description.{locale}": search_regex}
            ]

        # --- Sort order ---
        sort_order = -1 if order == SortOrder.DESC else 1

        # --- Count total ---
        total_data = self.collection.count_documents(query)

        # --- Apply pagination ---
        cursor = (
            self.collection.find(query)
            .sort("_id", sort_order)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )

        data = list(cursor)
        return data, total_data

    def get_all_tags(self, limit: int = 50):
        """
        Retrieve all unique tags from the gallery collection, limited by 'limit'.
        Uses MongoDB aggregation to unwind and group tags efficiently.
        """
        pipeline = [
            {"$unwind": "$tags"},                 # break apart tag arrays
            {"$group": {"_id": "$tags"}},         # group unique tags
            {"$sample": {"size": limit}}          # randomize selection (limit applied here)
        ]

        results = list(self.collection.aggregate(pipeline))
        # Convert MongoDB _id results into plain list of tag strings
        tags = [r["_id"] for r in results]
        return tags

