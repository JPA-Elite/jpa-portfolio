from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.Interfaces.IActivityLogRepository import IActivityLogRepository
from app.constants.db_collections import MongoCollections as mc

class ActivityLogRepository(IActivityLogRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.ACTIVITY_LOGS)

    def insert(self, entry: dict):
        return self.collection.insert_one(entry)
