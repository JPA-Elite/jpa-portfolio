from datetime import datetime, timedelta
from flask import request
from Repositories.BaseRepository import BaseRepository
from constants.db_collections import MongoCollections as mc
from Repositories.Interfaces.ILoginAttemptRepository import ILoginAttemptRepository

MAX_ATTEMPTS = 3
LOCKOUT_HOURS = 1

class LoginAttemptRepository(ILoginAttemptRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.LOGIN_ATTEMPTS)  # use "login_attempts" collection

    def _get_client_ip(self):
        """Get client IP address safely (supports proxy environments)."""
        if request.headers.get("X-Forwarded-For"):
            # If app is behind proxy (like Render), this header stores real client IP
            ip = request.headers.get("X-Forwarded-For").split(",")[0].strip()
        else:
            ip = request.remote_addr or "unknown_ip"
        return ip

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
