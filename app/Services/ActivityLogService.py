from app.Models.ActivityLog import ActivityLog
from app.Repositories.Interfaces.IActivityLogRepository import IActivityLogRepository


class ActivityLogService:
    def __init__(self, repository: IActivityLogRepository):
        self.repository = repository

    def log_admin_activity(self, entry: dict):
        return self.repository.insert(ActivityLog.from_dict(entry).to_dict())

    def delete_by_ids(self, record_ids: list):
        return self.repository.delete_by_ids(record_ids)

    def delete_all(self):
        return self.repository.delete_all()

    def get_paginated(self, page=1, per_page=10, order=None, search=""):
        return self.repository.get_paginated(page, per_page, order, search)

    def find_recent(self, limit=50):
        return self.repository.find_recent(limit)
