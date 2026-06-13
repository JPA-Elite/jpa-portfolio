from app.Repositories.Interfaces.IVideoRepository import IVideoRepository
from app.Repositories.BaseRepository import BaseRepository
from app.configurations import SortOrder
from app.constants.db_collections import MongoCollections as mc
from bson import ObjectId
from app.Models.Video import Video
from bson.regex import Regex

class VideoRepository(IVideoRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VIDEO)

    def get_video_by_id(self, video_id: str):
        return self.collection.find_one({"_id": ObjectId(video_id)})

    def get_paginated_video_list(self, page: int, per_page: int, order: SortOrder):
        sort_order = -1 if order == SortOrder.DESC else 1

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
        result = self.collection.insert_one(video.to_dict())
        return str(result.inserted_id)

    def update_video(self, video_id: str, video: Video):
        result = self.collection.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": video.to_dict()}
        )
        return result.matched_count > 0

    def delete_video(self, video_id: str):
        result = self.collection.delete_one({"_id": ObjectId(video_id)})
        return result.deleted_count > 0

    def search_video_paginated(
        self,
        search_query: str = "",
        tags=None,
        locale: str = "en",
        page: int = 1,
        per_page: int = 10,
        order: SortOrder = SortOrder.DESC
    ):
        query = {}

        if tags:
            if isinstance(tags, str):
                tags = tags.split('.')
            elif not isinstance(tags, list):
                tags = [tags]
            query["tags"] = {"$in": tags}

        if search_query:
            search_regex = Regex(search_query, "i")
            query["$or"] = [
                {f"title.{locale}": search_regex},
                {f"description.{locale}": search_regex}
            ]

        sort_order = -1 if order == SortOrder.DESC else 1

        total_data = self.collection.count_documents(query)

        cursor = (
            self.collection.find(query)
            .sort("_id", sort_order)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )

        data = list(cursor)
        return data, total_data

    def get_all_tags(self, limit: int = 50):
        pipeline = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags"}},
            {"$sample": {"size": limit}}
        ]

        results = list(self.collection.aggregate(pipeline))
        tags = [r["_id"] for r in results]
        return tags

