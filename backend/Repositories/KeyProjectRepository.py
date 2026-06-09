from bson import ObjectId
import re
from backend.Repositories.Interfaces.IKeyProjectRepository import IKeyProjectRepository
from backend.Repositories.BaseRepository import BaseRepository
from backend.constants.db_collections import MongoCollections as mc
from backend.configurations import SortOrder
from backend.Models.KeyProject import KeyProject

class KeyProjectRepository(IKeyProjectRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.KEY_PROJECTS)

    def get_key_project_by_id(self, project_id: str):
        return self.collection.find_one({"_id": ObjectId(project_id)})

    def get_paginated_key_projects(
        self,
        page: int,
        per_page: int,
        order: SortOrder,
        search_query: str = "",
        status_filter: str = "",
        is_active_filter=None,
    ):
        sort_direction = -1 if order == SortOrder.DESC else 1

        query_conditions = []
        if search_query:
            escaped = re.escape(search_query.strip())
            query_conditions.append({
                "$or": [
                    {"title.en": {"$regex": escaped, "$options": "i"}},
                    {"title.ceb": {"$regex": escaped, "$options": "i"}},
                    {"title.fr": {"$regex": escaped, "$options": "i"}},
                    {"title.fil_PH": {"$regex": escaped, "$options": "i"}},
                    {"description.en": {"$regex": escaped, "$options": "i"}},
                    {"description.ceb": {"$regex": escaped, "$options": "i"}},
                    {"description.fr": {"$regex": escaped, "$options": "i"}},
                    {"description.fil_PH": {"$regex": escaped, "$options": "i"}},
                    {"stack": {"$regex": escaped, "$options": "i"}},
                    {"status": {"$regex": escaped, "$options": "i"}},
                    {"demo_url": {"$regex": escaped, "$options": "i"}},
                    {"repo_url": {"$regex": escaped, "$options": "i"}},
                ]
            })

        normalized_status = (status_filter or "").strip().lower()
        if normalized_status in {"shipped", "building", "planned"}:
            query_conditions.append({"status": normalized_status})

        if is_active_filter is True or is_active_filter is False:
            query_conditions.append({"is_active": is_active_filter})

        if not query_conditions:
            query = {}
        elif len(query_conditions) == 1:
            query = query_conditions[0]
        else:
            query = {"$and": query_conditions}

        cursor = (
            self.collection.find(query)
            .sort([("sort_order", 1), ("_id", sort_direction)])
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        data = list(cursor)
        total = self.collection.count_documents(query)
        return data, total

    def get_active_key_projects(self):
        cursor = (
            self.collection.find({"is_active": {"$ne": False}})
            .sort([("sort_order", 1), ("_id", -1)])
        )
        return list(cursor)

    def count_key_projects(self):
        return self.collection.count_documents({})

    def add_key_project(self, key_project: KeyProject):
        result = self.collection.insert_one(key_project.to_dict())
        return str(result.inserted_id)

    def add_many_key_projects(self, key_projects: list[KeyProject]):
        if not key_projects:
            return []
        result = self.collection.insert_many([p.to_dict() for p in key_projects])
        return [str(x) for x in result.inserted_ids]

    def update_key_project(self, project_id: str, key_project: KeyProject):
        result = self.collection.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": key_project.to_dict()},
        )
        return result.matched_count > 0

    def delete_key_project(self, project_id: str):
        result = self.collection.delete_one({"_id": ObjectId(project_id)})
        return result.deleted_count > 0

