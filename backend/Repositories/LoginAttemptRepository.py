from datetime import datetime, timedelta
from flask import request
import re
from backend.Repositories.BaseRepository import BaseRepository
from backend.constants.db_collections import MongoCollections as mc
from backend.Repositories.Interfaces.ILoginAttemptRepository import ILoginAttemptRepository
from bson import ObjectId, errors as bson_errors
from backend.configurations import SortOrder
from backend.security import get_request_ip

MAX_ATTEMPTS = 3
LOCKOUT_HOURS = 1

class LoginAttemptRepository(ILoginAttemptRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.LOGIN_ATTEMPTS)  # use "login_attempts" collection

    def _get_client_ip(self):
        """Get client IP address safely (supports proxy environments)."""
        return get_request_ip() or (request.remote_addr or "unknown_ip")

    def get_attempt_info(self):
        """Retrieve attempt info based on client IP."""
        client_ip = self._get_client_ip()
        data = self.collection.find_one({"_id": client_ip})

        if not data:
            data = {"_id": client_ip, "attempts": 0, "lockout_until": None}
            self.collection.insert_one(data)
        return data

    def update_attempt(self, success=False):
        """Update attempt count for a specific client IP."""
        now = datetime.utcnow()
        client_ip = self._get_client_ip()
        attempt = self.get_attempt_info()

        if success:
            update_data = {"attempts": 0, "lockout_until": None}  # ✅ Reset on success
        else:
            attempts = attempt.get("attempts", 0) + 1
            lockout_until = attempt.get("lockout_until")

            if attempts >= MAX_ATTEMPTS:
                lockout_until = now.replace(microsecond=0) + timedelta(hours=LOCKOUT_HOURS)

            update_data = {"attempts": attempts, "lockout_until": lockout_until}

        self.collection.update_one(
            {"_id": client_ip},
            {"$set": update_data},
            upsert=True
        )

        return update_data

    def get_login_attempt_by_id(self, login_attempt_id: str):
        """Fetch a login_attempt document by _id (supports both ObjectId and string IP)."""
        try:
            query = {"_id": ObjectId(login_attempt_id)}
        except bson_errors.InvalidId:
            query = {"_id": login_attempt_id}

        return self.collection.find_one(query)

    def get_paginated_login_attempt_list(
        self,
        page: int,
        per_page: int,
        order: SortOrder,
        search_query: str = "",
    ):
        # Mongo sort order by _id
        sort_order = -1 if order == SortOrder.DESC else 1
        query = {}

        if search_query:
            escaped = re.escape(search_query.strip())
            or_filters = [
                {"_id": {"$regex": escaped, "$options": "i"}},
            ]
            if search_query.strip().isdigit():
                or_filters.append({"attempts": int(search_query.strip())})
            query = {"$or": or_filters}

        # Use MongoDB skip + limit for pagination
        cursor = (
            self.collection.find(query)
            .sort("_id", sort_order)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )

        data = list(cursor)
        total_data = self.collection.count_documents(query)

        return data, total_data

    def delete_login_attempt(self, login_attempt_id: str):
        """Delete a login_attempt document by _id (IP or ObjectId)."""
        try:
            query = {"_id": ObjectId(login_attempt_id)}
        except bson_errors.InvalidId:
            query = {"_id": login_attempt_id}

        result = self.collection.delete_one(query)
        return result.deleted_count > 0
