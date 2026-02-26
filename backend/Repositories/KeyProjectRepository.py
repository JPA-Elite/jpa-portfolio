from bson import ObjectId

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

    def get_paginated_key_projects(self, page: int, per_page: int, order: SortOrder):
        sort_direction = -1 if order == SortOrder.DESC else 1
        cursor = (
            self.collection.find()
            .sort([("sort_order", 1), ("_id", sort_direction)])
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        data = list(cursor)
        total = self.collection.count_documents({})
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
