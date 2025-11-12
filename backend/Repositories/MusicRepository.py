from Repositories.Interfaces.IMusicRepository import IMusicRepository
from Repositories.BaseRepository import BaseRepository
from config import SortOrder
from constants.db_collections import MongoCollections as mc
from bson import ObjectId
from Models.Music import Music

class MusicRepository(IMusicRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.MUSIC)  # use "music" collection

    def get_music_by_id(self, music_id: str):
        """Fetch a music document by _id."""
        return self.collection.find_one({"_id": ObjectId(music_id)})

    def get_paginated_music_list(self, page: int, per_page: int, order: SortOrder):
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

    def add_music(self, music: Music):
        """Insert a new music document into MongoDB."""
        result = self.collection.insert_one(music.to_dict())
        return str(result.inserted_id)

    def update_music(self, music_id: str, music: Music):
        """Update a music document by _id."""
        result = self.collection.update_one(
            {"_id": ObjectId(music_id)},
            {"$set": music.to_dict()}
        )
        return result.matched_count > 0  # True if updated

    def delete_music(self, music_id: str):
        """Delete a music document by _id."""
        result = self.collection.delete_one({"_id": ObjectId(music_id)})
        return result.deleted_count > 0  # True if deleted
