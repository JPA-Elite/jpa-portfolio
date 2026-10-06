from bson import ObjectId
from bson.errors import InvalidId
from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.Interfaces.IActivityLogRepository import IActivityLogRepository
from app.configurations import SortOrder
from app.constants.db_collections import MongoCollections as mc
import re


class ActivityLogRepository(IActivityLogRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.ACTIVITY_LOGS)

    def insert(self, entry: dict):
        return self.insert_one(entry)

    def delete_by_ids(self, record_ids: list):
        if not record_ids:
            result = self.delete_many({})
            return {"status": "success", "deleted_count": result.deleted_count}
        object_ids = []
        for rid in record_ids:
            try:
                object_ids.append(ObjectId(str(rid)))
            except (InvalidId, TypeError):
                continue
        if not object_ids:
            return {"status": "error", "message": "Invalid record IDs."}
        result = self.delete_many({"_id": {"$in": object_ids}})
        if not result.deleted_count:
            return {"status": "error", "message": "Activity record not found."}
        return {"status": "success", "deleted_count": result.deleted_count}

    def delete_all(self):
        result = self.delete_many({})
        return {"status": "success", "deleted_count": result.deleted_count}

    def count_by_query(self, query: dict):
        return int(self.count_documents(query or {}))

    def find_recent(self, limit: int = 50):
        docs = self.find(
            {},
            projection={},
            sort=[("_id", -1)],
            limit=int(limit),
        )
        for doc in docs:
            doc["_id"] = str(doc.get("_id"))
        return docs

    def build_search_query(self, search: str = ""):
        needle = str(search or "").strip()
        if not needle:
            return {}
        pattern = re.escape(needle)
        return {
            "$or": [
                {"method": {"$regex": pattern, "$options": "i"}},
                {"path": {"$regex": pattern, "$options": "i"}},
                {"user_id": {"$regex": pattern, "$options": "i"}},
                {"remote_addr": {"$regex": pattern, "$options": "i"}},
                {"timestamp": {"$regex": pattern, "$options": "i"}},
            ]
        }

    def get_paginated(self, page=1, per_page=10, order=None, search: str = ""):
        try:
            page = max(1, int(page))
        except (TypeError, ValueError):
            page = 1
        try:
            per_page = int(per_page)
        except (TypeError, ValueError):
            per_page = 10
        per_page = max(1, min(per_page, 100))
        query = self.build_search_query(search)
        total = int(self.count_documents(query))
        if total == 0:
            return [], 0
        sort_direction = -1 if order == SortOrder.DESC else 1
        skip = (page - 1) * per_page
        projection = {"method": 1, "path": 1, "status_code": 1, "user_id": 1, "user": 1, "timestamp": 1, "body": 1, "remote_addr": 1}
        docs = self.find(
            query,
            projection=projection,
            sort=[("_id", sort_direction)],
            skip=skip,
            limit=per_page,
        )
        for doc in docs:
            doc["_id"] = str(doc.get("_id"))
        return docs, total
