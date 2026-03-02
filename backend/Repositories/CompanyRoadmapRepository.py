from bson import ObjectId

from Repositories.Interfaces.ICompanyRoadmapRepository import ICompanyRoadmapRepository
from Repositories.BaseRepository import BaseRepository
from constants.db_collections import MongoCollections as mc
from configurations import SortOrder
from Models.CompanyRoadmap import CompanyRoadmap


class CompanyRoadmapRepository(ICompanyRoadmapRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.COMPANY_ROADMAPS)

    def get_company_roadmap_by_id(self, roadmap_id: str):
        return self.collection.find_one({"_id": ObjectId(roadmap_id)})

    def get_paginated_company_roadmaps(self, page: int, per_page: int, order: SortOrder):
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

    def get_active_company_roadmaps(self):
        cursor = (
            self.collection.find({"is_active": {"$ne": False}})
            .sort([("sort_order", 1), ("_id", -1)])
        )
        return list(cursor)

    def count_company_roadmaps(self):
        return self.collection.count_documents({})

    def add_company_roadmap(self, roadmap: CompanyRoadmap):
        result = self.collection.insert_one(roadmap.to_dict())
        return str(result.inserted_id)

    def add_many_company_roadmaps(self, roadmaps: list[CompanyRoadmap]):
        if not roadmaps:
            return []
        result = self.collection.insert_many([r.to_dict() for r in roadmaps])
        return [str(x) for x in result.inserted_ids]

    def update_company_roadmap(self, roadmap_id: str, roadmap: CompanyRoadmap):
        result = self.collection.update_one(
            {"_id": ObjectId(roadmap_id)},
            {"$set": roadmap.to_dict()},
        )
        return result.matched_count > 0

    def delete_company_roadmap(self, roadmap_id: str):
        result = self.collection.delete_one({"_id": ObjectId(roadmap_id)})
        return result.deleted_count > 0
