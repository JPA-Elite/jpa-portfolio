from backend.Repositories.BaseRepository import BaseRepository
from backend.constants.db_collections import MongoCollections as mc

class ActivityLogRepository(BaseRepository):
    def __init__(self):
        super().__init__(mc.ACTIVITY_LOGS)

    def insert(self, entry: dict):
        """Insert an activity log entry into MongoDB."""
        return self.collection.insert_one(entry)
