from Repositories.Interfaces.IVideoRepository import IVideoRepository
from Repositories.BaseRepository import BaseRepository
from config import SortOrder
from constants.db_collections import MongoCollections as mc
from bson import ObjectId
from Models.Video import Video

class VideoRepository(IVideoRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VIDEO)  # use "video" collection

    def get_video_by_id(self, video_id: str):
        """Fetch a video document by _id."""
        return self.collection.find_one({"_id": ObjectId(video_id)})

    def get_paginated_video_list(self, page: int, per_page: int, order: SortOrder):
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

    def add_video(self, video: Video):
        """Insert a new video document into MongoDB."""
        result = self.collection.insert_one(video.to_dict())
        return str(result.inserted_id)

    def update_video(self, video_id: str, video: Video):
        """Update a video document by _id."""
        result = self.collection.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": video.to_dict()}
        )
        return result.matched_count > 0  # True if updated

    def delete_video(self, video_id: str):
        """Delete a video document by _id."""
        result = self.collection.delete_one({"_id": ObjectId(video_id)})
        return result.deleted_count > 0  # True if deleted
