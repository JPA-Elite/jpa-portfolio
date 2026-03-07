from datetime import datetime
import re

from bson import ObjectId

from backend.Repositories.BaseRepository import BaseRepository
from backend.constants.db_collections import MongoCollections as mc


class ServerFileRepository(BaseRepository):
    def __init__(self):
        super().__init__(mc.SERVER_FILES)
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            self.collection.create_index("channel_id")
            self.collection.create_index("uploaded_by_user_id")
            self.collection.create_index("created_at")
        except Exception:
            pass

    @staticmethod
    def _normalize_pagination(page: int, per_page: int):
        safe_page = max(1, int(page or 1))
        safe_per_page = max(1, min(int(per_page or 50), 100))
        return safe_page, safe_per_page

    def add_file(self, data: dict):
        payload = dict(data or {})
        payload.setdefault("created_at", datetime.utcnow())
        payload.setdefault("updated_at", datetime.utcnow())
        payload.setdefault("is_deleted", False)
        result = self.collection.insert_one(payload)
        return str(result.inserted_id)

    def get_file_by_id(self, file_id: str):
        try:
            return self.collection.find_one({"_id": ObjectId(file_id)})
        except Exception:
            return None

    def update_file(self, file_id: str, data: dict):
        payload = dict(data or {})
        payload["updated_at"] = datetime.utcnow()
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(file_id)},
                {"$set": payload},
            )
        except Exception:
            return False
        return result.matched_count > 0

    def delete_file(self, file_id: str):
        try:
            result = self.collection.delete_one({"_id": ObjectId(file_id)})
        except Exception:
            return False
        return result.deleted_count > 0

    def count_files_for_channel(self, channel_id: str):
        return self.collection.count_documents(
            {
                "channel_id": str(channel_id),
                "is_deleted": {"$ne": True},
            }
        )

    def count_files_for_channels(self, channel_ids):
        normalized_ids = [str(value) for value in (channel_ids or []) if str(value).strip()]
        if not normalized_ids:
            return {}

        pipeline = [
            {
                "$match": {
                    "channel_id": {"$in": normalized_ids},
                    "is_deleted": {"$ne": True},
                }
            },
            {
                "$group": {
                    "_id": "$channel_id",
                    "count": {"$sum": 1},
                }
            },
        ]
        payload = {}
        for item in self.collection.aggregate(pipeline):
            payload[str(item.get("_id") or "")] = int(item.get("count") or 0)
        return payload

    def get_files_page(
        self,
        channel_id: str,
        *,
        page: int = 1,
        per_page: int = 50,
        search_query: str = "",
    ):
        safe_page, safe_per_page = self._normalize_pagination(page, per_page)
        conditions = [
            {"channel_id": str(channel_id)},
            {"is_deleted": {"$ne": True}},
        ]

        normalized_search = str(search_query or "").strip()
        if normalized_search:
            escaped = re.escape(normalized_search)
            regex = {"$regex": escaped, "$options": "i"}
            conditions.append(
                {
                    "$or": [
                        {"name": regex},
                        {"uploaded_by_username": regex},
                        {"original_filename": regex},
                    ]
                }
            )

        query = conditions[0] if len(conditions) == 1 else {"$and": conditions}
        total = self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort([("created_at", -1), ("_id", -1)])
            .skip((safe_page - 1) * safe_per_page)
            .limit(safe_per_page)
        )
        return list(cursor), total
