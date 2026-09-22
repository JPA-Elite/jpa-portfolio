from bson import ObjectId
import re
from app.Repositories.Interfaces.IBuiltAppRepository import IBuiltAppRepository
from app.Repositories.BaseRepository import BaseRepository
from app.constants.db_collections import MongoCollections as mc
from app.configurations import SortOrder
from app.Models.BuiltApp import BuiltApp

class BuiltAppRepository(IBuiltAppRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.BUILT_APPS)

    def get_built_app_by_id(self, app_id: str):
        return self.find_one({"_id": ObjectId(app_id)})

    def get_paginated_built_apps(
        self,
        page: int,
        per_page: int,
        order: SortOrder,
        search_query: str = "",
        platform_filter: str = "",
        is_active_filter=None,
    ):
        sort_direction = -1 if order == SortOrder.DESC else 1

        query_conditions = []
        if search_query:
            escaped = re.escape(search_query.strip())
            query_conditions.append({
                "$or": [
                    {"name.en": {"$regex": escaped, "$options": "i"}},
                    {"name.ceb": {"$regex": escaped, "$options": "i"}},
                    {"name.fr": {"$regex": escaped, "$options": "i"}},
                    {"name.fil_PH": {"$regex": escaped, "$options": "i"}},
                    {"short_description.en": {"$regex": escaped, "$options": "i"}},
                    {"slug": {"$regex": escaped, "$options": "i"}},
                    {"platform": {"$regex": escaped, "$options": "i"}},
                    {"version": {"$regex": escaped, "$options": "i"}},
                ]
            })

        normalized_platform = (platform_filter or "").strip().lower()
        if normalized_platform in {"mobile", "desktop"}:
            query_conditions.append({"platform": normalized_platform.capitalize()})

        if is_active_filter is True or is_active_filter is False:
            query_conditions.append({"is_active": is_active_filter})

        if not query_conditions:
            query = {}
        elif len(query_conditions) == 1:
            query = query_conditions[0]
        else:
            query = {"$and": query_conditions}

        data = self.find(
            query,
            sort=[("sort_order", 1), ("_id", sort_direction)],
            skip=(page - 1) * per_page,
            limit=per_page,
        )
        total = self.count_documents(query)
        return data, total

    def get_active_built_apps(self):
        return self.find(
            {"is_active": {"$ne": False}},
            sort=[("sort_order", 1), ("_id", -1)],
        )

    def find_active_built_app_by_slug(self, slug: str):
        return self.find_one({
            "slug": str(slug or "").strip().lower(),
            "is_active": {"$ne": False},
        })

    def count_built_apps(self):
        return self.count_documents({})

    def add_built_app(self, built_app: BuiltApp):
        result = self.insert_one(built_app.to_dict())
        return str(result.inserted_id)

    def add_many_built_apps(self, built_apps: list[BuiltApp]):
        if not built_apps:
            return []
        result = self.insert_many([a.to_dict() for a in built_apps])
        return [str(x) for x in result.inserted_ids]

    def update_built_app(self, app_id: str, built_app: BuiltApp):
        result = self.update_one(
            {"_id": ObjectId(app_id)},
            {"$set": built_app.to_dict()},
        )
        return result.matched_count > 0

    def delete_built_app(self, app_id: str):
        result = self.delete_one({"_id": ObjectId(app_id)})
        return result.deleted_count > 0
