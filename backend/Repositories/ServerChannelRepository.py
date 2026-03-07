from datetime import datetime
import re

from bson import ObjectId

from backend.Repositories.BaseRepository import BaseRepository
from backend.constants.db_collections import MongoCollections as mc
from backend.configurations import SortOrder


class ServerChannelRepository(BaseRepository):
    def __init__(self):
        super().__init__(mc.SERVER_CHANNELS)
        self._ensure_indexes()

    def _ensure_indexes(self):
        try:
            self.collection.create_index("slug", unique=True)
            self.collection.create_index("is_public")
            self.collection.create_index("member_ids")
            self.collection.create_index("channel_type")
        except Exception:
            pass

    def ensure_default_channels(self):
        self._upsert_default_channel(
            slug="general",
            name="general",
            description="General discussion for everyone.",
            channel_type="general",
            is_public=True,
        )
        self._upsert_default_channel(
            slug="business-concerns",
            name="business concerns",
            description="Business-related concerns and updates.",
            channel_type="business",
            is_public=True,
        )

    def _upsert_default_channel(self, slug, name, description, channel_type, is_public):
        now = datetime.utcnow()
        self.collection.update_one(
            {"slug": slug},
            {
                "$setOnInsert": {
                    "name": name,
                    "slug": slug,
                    "description": description,
                    "channel_type": channel_type,
                    "is_public": is_public,
                    "member_ids": [],
                    "created_at": now,
                },
                "$set": {
                    "updated_at": now,
                },
            },
            upsert=True,
        )

    def add_channel(self, data: dict):
        payload = dict(data or {})
        payload.setdefault("created_at", datetime.utcnow())
        payload.setdefault("updated_at", datetime.utcnow())
        payload.setdefault("member_ids", [])
        result = self.collection.insert_one(payload)
        return str(result.inserted_id)

    def get_channel_by_id(self, channel_id: str):
        try:
            return self.collection.find_one({"_id": ObjectId(channel_id)})
        except Exception:
            return None

    def get_channel_by_slug(self, slug: str):
        return self.collection.find_one({"slug": str(slug or "").strip()})

    def get_channel_by_user(self, user_id: str):
        return self.collection.find_one(
            {
                "channel_type": "concern",
                "owner_user_id": str(user_id or "").strip(),
            }
        )

    def update_channel(self, channel_id: str, data: dict):
        payload = dict(data or {})
        payload["updated_at"] = datetime.utcnow()
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(channel_id)},
                {"$set": payload},
            )
        except Exception:
            return False
        return result.matched_count > 0

    def delete_channel(self, channel_id: str):
        try:
            result = self.collection.delete_one({"_id": ObjectId(channel_id)})
        except Exception:
            return False
        return result.deleted_count > 0

    def list_channels_for_user(self, user_id: str, account_type: str):
        if str(account_type or "").lower() == "admin":
            cursor = self.collection.find({}).sort([("name", 1), ("_id", 1)])
            return list(cursor)

        cursor = self.collection.find(
            {
                "$or": [
                    {"is_public": True},
                    {"member_ids": str(user_id)},
                ]
            }
        ).sort([("name", 1), ("_id", 1)])
        return list(cursor)

    def get_paginated_channels(
        self,
        page: int,
        per_page: int,
        order: SortOrder,
        search_query: str = "",
        type_filter: str = "",
        visibility_filter: str = "",
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
                        {"slug": {"$regex": escaped, "$options": "i"}},
                        {"description": {"$regex": escaped, "$options": "i"}},
                        {"channel_type": {"$regex": escaped, "$options": "i"}},
                    ]
                }
            )

        normalized_type = str(type_filter or "").strip().lower()
        if normalized_type:
            query_conditions.append({"channel_type": normalized_type})

        normalized_visibility = str(visibility_filter or "").strip().lower()
        if normalized_visibility in {"public", "private"}:
            query_conditions.append({"is_public": normalized_visibility == "public"})

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

    @staticmethod
    def slugify(value: str):
        raw = str(value or "").strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
        return slug or "channel"
