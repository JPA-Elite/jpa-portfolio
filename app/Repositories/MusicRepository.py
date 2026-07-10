import re
from app.Repositories.Interfaces.IMusicRepository import IMusicRepository
from app.Repositories.BaseRepository import BaseRepository
from app.configurations import SortOrder
from app.constants.db_collections import MongoCollections as mc
from bson import ObjectId
from app.Models.Music import Music

class MusicRepository(IMusicRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.MUSIC)

    def get_music_by_id(self, music_id: str):
        return self.find_one({"_id": ObjectId(music_id)})

    def get_music_by_url(self, music_url: str):
        return self.find_one({"url": music_url})

    def get_paginated_music_list(self, page: int, per_page: int, order: SortOrder, search_query: str = "", category: str = ""):
        sort_order = -1 if order == SortOrder.DESC else 1
        query = {}

        # Build query based on search and category filters
        if search_query or category:
            query = {}
            conditions = []

            if search_query:
                escaped = re.escape(search_query.strip())
                conditions.append({
                    "$or": [
                        {"title": {"$regex": escaped, "$options": "i"}},
                        {"artist": {"$regex": escaped, "$options": "i"}},
                    ]
                })

            if category and category != "All":
                conditions.append({"category": category})

            if conditions:
                query = {"$and": conditions} if len(conditions) > 1 else conditions[0]

        data = self.find(
            query,
            sort=[("_id", sort_order)],
            skip=(page - 1) * per_page,
            limit=per_page,
        )

        total_data = self.count_documents(query)

        return data, total_data

    def get_all_categories(self):
        """Get all unique categories from the database"""
        return self.collection.distinct("category")

    def get_category_counts(self):
        """Get count of music grouped by category"""
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        result = self.aggregate(pipeline)
        return {item["_id"]: item["count"] for item in result}

    def add_music(self, music: Music):
        result = self.insert_one(music.to_dict())
        return str(result.inserted_id)

    def update_music(self, music_id: str, music: Music):
        result = self.update_one(
            {"_id": ObjectId(music_id)},
            {"$set": music.to_dict()}
        )
        return result.matched_count > 0

    def delete_music(self, music_id: str):
        result = self.delete_one({"_id": ObjectId(music_id)})
        return result.deleted_count > 0

    def get_total_music_count(self) -> int:
        return self.count_documents({})

