from datetime import datetime
import re

from bson import ObjectId

from backend.Repositories.BaseRepository import BaseRepository
from backend.constants.db_collections import MongoCollections as mc
from backend.configurations import SortOrder


class ServerUserRepository(BaseRepository):
    def __init__(self):
        super().__init__(mc.SERVER_USERS)
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            self.collection.create_index("username_lower", unique=True)
            self.collection.create_index("email_lower", unique=True)
            self.collection.create_index("google_uid", unique=True, sparse=True)
            self.collection.create_index("account_type")
            self.collection.create_index("is_online")
            self.collection.create_index("last_active_at")
            self.collection.create_index("password_reset_otp_expires_at")
        except Exception:
            # Non-blocking in constrained/mock environments.
            pass

    def add_user(self, data: dict):
        payload = dict(data or {})
        payload.setdefault("created_at", datetime.utcnow())
        payload.setdefault("updated_at", datetime.utcnow())
        result = self.collection.insert_one(payload)
        return str(result.inserted_id)

    def get_user_by_id(self, user_id: str):
        try:
            return self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

    def find_by_username(self, username: str):
        return self.collection.find_one({"username_lower": str(username or "").strip().lower()})

    def find_by_email(self, email: str):
        return self.collection.find_one({"email_lower": str(email or "").strip().lower()})

    def find_by_login(self, login_value: str):
        value = str(login_value or "").strip().lower()
        return self.collection.find_one(
            {
                "$or": [
                    {"username_lower": value},
                    {"email_lower": value},
                ]
            }
        )

    def get_users_by_ids(self, user_ids):
        object_ids = []
        for user_id in user_ids or []:
            try:
                object_ids.append(ObjectId(str(user_id)))
            except Exception:
                continue
        if not object_ids:
            return []
        return list(self.collection.find({"_id": {"$in": object_ids}}))

    def list_active_users(self):
        return list(self.collection.find({"is_active": {"$ne": False}}))

    def get_server_admin_user_ids(self):
        cursor = self.collection.find(
            {
                "account_type": "admin",
                "is_active": {"$ne": False},
            },
            {"_id": 1},
        )
        return [str(item["_id"]) for item in cursor if item.get("_id")]

    def count_admin_accounts(self):
        return self.collection.count_documents({"account_type": "admin"})

    def update_user(self, user_id: str, data: dict):
        payload = dict(data or {})
        payload["updated_at"] = datetime.utcnow()
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": payload},
            )
        except Exception:
            return False
        return result.matched_count > 0

    def touch_last_active(self, user_id: str):
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "last_active_at": datetime.utcnow(),
                        "is_online": True,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
        except Exception:
            return False
        return result.matched_count > 0

    def set_online_status(self, user_id: str, is_online: bool):
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_online": bool(is_online),
                        "last_active_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
        except Exception:
            return False
        return result.matched_count > 0

    def delete_user(self, user_id: str):
        try:
            result = self.collection.delete_one({"_id": ObjectId(user_id)})
        except Exception:
            return False
        return result.deleted_count > 0

    def get_paginated_users(
        self,
        page: int,
        per_page: int,
        order: SortOrder,
        search_query: str = "",
        account_type_filter: str = "",
    ):
        sort_direction = -1 if order == SortOrder.DESC else 1
        query_conditions = []

        normalized_search = str(search_query or "").strip()
        if normalized_search:
            escaped = re.escape(normalized_search)
            query_conditions.append(
                {
                    "$or": [
                        {"name": {"$regex": escaped, "$options": "i"}},
                        {"username": {"$regex": escaped, "$options": "i"}},
                        {"email": {"$regex": escaped, "$options": "i"}},
                        {"place": {"$regex": escaped, "$options": "i"}},
                        {"gender": {"$regex": escaped, "$options": "i"}},
                    ]
                }
            )

        normalized_type = str(account_type_filter or "").strip().lower()
        if normalized_type in {"admin", "member"}:
            query_conditions.append({"account_type": normalized_type})

        if not query_conditions:
            query = {}
        elif len(query_conditions) == 1:
            query = query_conditions[0]
        else:
            query = {"$and": query_conditions}

        cursor = (
            self.collection.find(query)
            .sort([("created_at", sort_direction), ("_id", sort_direction)])
            .skip((page - 1) * per_page)
            .limit(per_page)
        )
        items = list(cursor)
        total = self.collection.count_documents(query)
        return items, total
