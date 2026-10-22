from app.Repositories.Interfaces.IVisitRepository import IVisitRepository
from app.Repositories.BaseRepository import BaseRepository
from datetime import datetime
from app.configurations import SortOrder
from app.constants.db_collections import MongoCollections as mc
import re

class VisitRepository(IVisitRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VISITORS)

    def _build_search_query(self, search: str = ""):
        needle = str(search or "").strip()
        if not needle:
            return {}
        pattern = re.escape(needle)
        searchable_fields = (
            "system", "device", "brand", "browser", "os", "page",
            "ip_address", "city", "region", "country", "location",
            "timestamp",
        )
        return {
            "$or": [
                {field: {"$regex": pattern, "$options": "i"}}
                for field in searchable_fields
            ]
        }

    def _legacy_paginated_documents(self, page, per_page, order: SortOrder, search: str = ""):
        all_documents = list(self.find())
        for doc in all_documents:
            if isinstance(doc.get("timestamp"), str):
                try:
                    doc["timestamp"] = datetime.strptime(doc["timestamp"], "%m/%d/%Y - %I:%M %p")
                except ValueError:
                    doc["timestamp"] = None

        documents = [doc for doc in all_documents if doc["timestamp"] is not None]

        needle = str(search or "").strip().lower()
        if needle:
            searchable_fields = (
                "system", "device", "brand", "browser", "os", "page",
                "ip_address", "city", "region", "country", "location",
            )
            documents = [
                doc for doc in documents
                if needle in doc["timestamp"].strftime("%m/%d/%Y - %I:%M %p").lower()
                or any(needle in str(doc.get(field) or "").lower() for field in searchable_fields)
            ]

        sorted_documents = sorted(
            documents,
            key=lambda x: x["timestamp"],
            reverse=(order == SortOrder.DESC),
        )

        start = (page - 1) * per_page
        end = start + per_page
        paginated_documents = sorted_documents[start:end]

        total_docs = len(sorted_documents)

        return paginated_documents, total_docs

    def get_paginated_documents(self, page, per_page, order: SortOrder, search: str = ""):
        try:
            page = max(1, int(page))
        except (TypeError, ValueError):
            page = 1
        try:
            per_page = int(per_page)
        except (TypeError, ValueError):
            per_page = 10
        per_page = max(1, min(int(per_page), 100))

        collection = getattr(self, "collection", None)
        if collection is None or not hasattr(collection, "count_documents"):
            return self._legacy_paginated_documents(page, per_page, order, search)

        try:
            query = self._build_search_query(search)
            total_docs = int(collection.count_documents(query))
            if total_docs == 0:
                return [], 0
            sort_direction = -1 if order == SortOrder.DESC else 1
            skip = (page - 1) * per_page
            cursor = (
                collection.find(query)
                .sort([("_id", sort_direction)])
                .skip(skip)
                .limit(per_page)
            )
            return list(cursor), total_docs
        except Exception:
            return self._legacy_paginated_documents(page, per_page, order, search)

    def delete_system_info_by_id(self, object_id):
        from bson import ObjectId
        if not isinstance(object_id, ObjectId):
            object_id = ObjectId(str(object_id))
        self.delete_one({"_id": object_id})

    def count_visits(self, where_condition: dict = None):
        if where_condition is None:
            where_condition = {}

        other_filter = {"$regex": "^other$", "$options": "i"}

        visitor_total_count = self.count_documents({
            **where_condition,
            "os": {"$not": other_filter}
        })

        bot_total_count = self.count_documents({
            **where_condition,
            "os": other_filter
        })

        return {
            "visitor_total_count": visitor_total_count,
            "bot_total_count": bot_total_count
        }

    def delete_all_visitors(self) -> dict:
        try:
            result = self.delete_many({})
            deleted_count = int(getattr(result, "deleted_count", 0))
            return {
                "status": "success",
                "message": f"Deleted {deleted_count} visitor record(s).",
                "deleted_count": deleted_count,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_visit_type_counts(self):
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": {
                            "$cond": [
                                {"$eq": [{"$toLower": "$os"}, "other"]},
                                "bot",
                                "visitor",
                            ]
                        },
                        "count": {"$sum": 1},
                    }
                }
            ]
            agg = list(self.aggregate(pipeline))
            counts = {"visitor_total_count": 0, "bot_total_count": 0}
            for entry in agg:
                if entry.get("_id") == "bot":
                    counts["bot_total_count"] = int(entry.get("count", 0))
                else:
                    counts["visitor_total_count"] = int(entry.get("count", 0))
            return counts
        except Exception:
            return self.count_visits()

    def find_all_image_captures(self):
        try:
            docs = self.find({}, projection={"image_capture": 1})
        except TypeError:
            docs = self.find({})
        return [doc.get("image_capture") for doc in docs if doc.get("image_capture")]

