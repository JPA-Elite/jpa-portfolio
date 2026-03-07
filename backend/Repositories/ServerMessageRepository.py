from datetime import datetime
import re
from bson import ObjectId

from backend.Repositories.BaseRepository import BaseRepository
from backend.constants.db_collections import MongoCollections as mc


class ServerMessageRepository(BaseRepository):
    def __init__(self):
        super().__init__(mc.SERVER_MESSAGES)
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            self.collection.create_index("channel_id")
            self.collection.create_index("parent_message_id")
            self.collection.create_index("created_at")
            self.collection.create_index("is_pinned")
            self.collection.create_index("mention_user_ids")
            self.collection.create_index("reaction_user_ids")
        except Exception:
            pass

    def add_message(self, data: dict):
        payload = dict(data or {})
        payload.setdefault("created_at", datetime.utcnow())
        result = self.collection.insert_one(payload)
        return str(result.inserted_id)

    def get_message_by_id(self, message_id: str):
        try:
            return self.collection.find_one({"_id": ObjectId(message_id)})
        except Exception:
            return None

    @staticmethod
    def _normalize_pagination(page: int, per_page: int):
        safe_page = max(1, int(page or 1))
        safe_per_page = max(1, min(int(per_page or 100), 500))
        return safe_page, safe_per_page

    @staticmethod
    def _safe_regex(search_query: str):
        query = str(search_query or "").strip()
        if not query:
            return None
        return {"$regex": re.escape(query), "$options": "i"}

    @staticmethod
    def _to_object_id_list(values):
        object_ids = []
        for value in values or []:
            try:
                object_ids.append(ObjectId(str(value)))
            except Exception:
                continue
        return object_ids

    def get_messages_page(
        self,
        channel_id: str,
        page: int = 1,
        per_page: int = 100,
        *,
        scope: str = "root",
        parent_message_id: str = "",
        search_query: str = "",
        pinned_only: bool = False,
        include_ids=None,
        sort_desc: bool = True,
    ):
        safe_page, safe_per_page = self._normalize_pagination(page, per_page)
        clauses = [{"channel_id": str(channel_id)}]

        include_object_ids = self._to_object_id_list(include_ids)
        root_filter = {
            "$or": [
                {"parent_message_id": {"$exists": False}},
                {"parent_message_id": None},
                {"parent_message_id": ""},
            ]
        }

        normalized_scope = str(scope or "root").strip().lower()
        if normalized_scope == "thread":
            clauses.append({"parent_message_id": str(parent_message_id or "").strip()})
        elif normalized_scope == "root":
            if include_object_ids:
                clauses.append(
                    {
                        "$or": [
                            root_filter,
                            {"_id": {"$in": include_object_ids}},
                        ]
                    }
                )
            else:
                clauses.append(root_filter)

        if pinned_only:
            clauses.append({"is_pinned": True})

        search_regex = self._safe_regex(search_query)
        if search_regex:
            if include_object_ids:
                clauses.append(
                    {
                        "$or": [
                            {"text": search_regex},
                            {"username": search_regex},
                            {"_id": {"$in": include_object_ids}},
                        ]
                    }
                )
            else:
                clauses.append({"$or": [{"text": search_regex}, {"username": search_regex}]})

        query = clauses[0] if len(clauses) == 1 else {"$and": clauses}
        sort_direction = -1 if sort_desc else 1
        total = self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort([("created_at", sort_direction), ("_id", sort_direction)])
            .skip((safe_page - 1) * safe_per_page)
            .limit(safe_per_page)
        )
        return list(cursor), total

    def find_parent_ids_for_reply_search(self, channel_id: str, search_query: str, limit: int = 2000):
        search_regex = self._safe_regex(search_query)
        if not search_regex:
            return []

        query = {
            "channel_id": str(channel_id),
            "parent_message_id": {"$type": "string", "$ne": ""},
            "$or": [{"text": search_regex}, {"username": search_regex}],
        }
        values = self.collection.distinct("parent_message_id", query)
        return [str(value) for value in values[: max(1, min(int(limit or 2000), 10000))]]

    def get_reply_stats_for_parents(self, channel_id: str, parent_ids):
        normalized_parent_ids = [str(value) for value in (parent_ids or []) if str(value).strip()]
        if not normalized_parent_ids:
            return {}

        pipeline = [
            {
                "$match": {
                    "channel_id": str(channel_id),
                    "parent_message_id": {"$in": normalized_parent_ids},
                }
            },
            {
                "$group": {
                    "_id": "$parent_message_id",
                    "reply_count": {"$sum": 1},
                    "last_reply_at": {"$max": "$created_at"},
                }
            },
        ]
        stats = {}
        for row in self.collection.aggregate(pipeline):
            parent_id = str(row.get("_id") or "")
            if not parent_id:
                continue
            stats[parent_id] = {
                "reply_count": int(row.get("reply_count") or 0),
                "last_reply_at": row.get("last_reply_at"),
            }
        return stats

    def get_messages_for_channels(
        self,
        channel_ids,
        page: int = 1,
        per_page: int = 20,
        *,
        filter_type: str = "all",
        current_user_id: str = "",
        current_username: str = "",
        sort_desc: bool = True,
    ):
        normalized_channel_ids = [
            str(value) for value in (channel_ids or []) if str(value).strip()
        ]
        if not normalized_channel_ids:
            return [], 0

        safe_page, safe_per_page = self._normalize_pagination(page, per_page)
        query = {
            "channel_id": {"$in": normalized_channel_ids},
            "is_deleted": {"$ne": True},
        }
        normalized_filter = str(filter_type or "all").strip().lower()
        if normalized_filter == "thread":
            query["parent_message_id"] = {"$type": "string", "$ne": ""}
        elif normalized_filter in {"mention", "@mentions"}:
            clauses = []
            normalized_user_id = str(current_user_id or "").strip()
            normalized_username = str(current_username or "").strip()
            if normalized_user_id:
                clauses.append({"mention_user_ids": normalized_user_id})
            if normalized_username:
                clauses.append(
                    {
                        "text": {
                            "$regex": rf"(?<![\\w])@{re.escape(normalized_username)}\\b",
                            "$options": "i",
                        }
                    }
                )
            if clauses:
                query["$or"] = clauses
            else:
                return [], 0
        elif normalized_filter in {"reaction", "@reactions"}:
            normalized_user_id = str(current_user_id or "").strip()
            if not normalized_user_id:
                return [], 0
            query["reaction_user_ids"] = normalized_user_id

        sort_direction = -1 if sort_desc else 1
        total = self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort([("created_at", sort_direction), ("_id", sort_direction)])
            .skip((safe_page - 1) * safe_per_page)
            .limit(safe_per_page)
        )
        return list(cursor), total

    def update_message(self, message_id: str, data: dict):
        payload = dict(data or {})
        payload["updated_at"] = datetime.utcnow()
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(message_id)},
                {"$set": payload},
            )
        except Exception:
            return False
        return result.matched_count > 0

    def delete_message(self, message_id: str):
        try:
            result = self.collection.delete_one({"_id": ObjectId(message_id)})
        except Exception:
            return False
        return result.deleted_count > 0

    def delete_messages_by_channel(self, channel_id: str):
        self.collection.delete_many({"channel_id": str(channel_id)})

    def delete_messages_by_user(self, user_id: str):
        self.collection.delete_many({"user_id": str(user_id)})
