from bson import ObjectId
import re
from app.Repositories.Interfaces.ICompanyRoadmapRepository import ICompanyRoadmapRepository
from app.Repositories.BaseRepository import BaseRepository
from app.constants.db_collections import MongoCollections as mc
from app.configurations import SortOrder
from app.Models.CompanyRoadmap import CompanyRoadmap

class CompanyRoadmapRepository(ICompanyRoadmapRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.COMPANY_ROADMAPS)

    def get_company_roadmap_by_id(self, roadmap_id: str):
        return self.collection.find_one({"_id": ObjectId(roadmap_id)})

    def get_paginated_company_roadmaps(
        self,
        page: int,
        per_page: int,
        order: SortOrder,
        search_query: str = "",
        employment_type_filter: str = "",
        is_active_filter=None,
    ):
        sort_direction = -1 if order == SortOrder.DESC else 1

        query_conditions = []
        if search_query:
            escaped = re.escape(search_query.strip())
            query_conditions.append({
                "$or": [
                    {"company_name": {"$regex": escaped, "$options": "i"}},
                    {"role_title": {"$regex": escaped, "$options": "i"}},
                    {"period": {"$regex": escaped, "$options": "i"}},
                    {"employment_type": {"$regex": escaped, "$options": "i"}},
                    {"location": {"$regex": escaped, "$options": "i"}},
                    {"definition": {"$regex": escaped, "$options": "i"}},
                    {"summary": {"$regex": escaped, "$options": "i"}},
                    {"role_title_i18n.en": {"$regex": escaped, "$options": "i"}},
                    {"role_title_i18n.ceb": {"$regex": escaped, "$options": "i"}},
                    {"role_title_i18n.fil_PH": {"$regex": escaped, "$options": "i"}},
                    {"definition_i18n.en": {"$regex": escaped, "$options": "i"}},
                    {"definition_i18n.ceb": {"$regex": escaped, "$options": "i"}},
                    {"definition_i18n.fil_PH": {"$regex": escaped, "$options": "i"}},
                    {"summary_i18n.en": {"$regex": escaped, "$options": "i"}},
                    {"summary_i18n.ceb": {"$regex": escaped, "$options": "i"}},
                    {"summary_i18n.fil_PH": {"$regex": escaped, "$options": "i"}},
                ]
            })

        normalized_employment_type = (employment_type_filter or "").strip()
        if normalized_employment_type:
            query_conditions.append({
                "employment_type": {
                    "$regex": f"^{re.escape(normalized_employment_type)}$",
                    "$options": "i",
                }
            })

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

