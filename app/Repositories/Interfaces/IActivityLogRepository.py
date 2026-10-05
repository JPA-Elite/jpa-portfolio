from abc import ABC, abstractmethod


class IActivityLogRepository(ABC):
    @abstractmethod
    def insert(self, entry: dict):
        pass

    @abstractmethod
    def delete_by_ids(self, record_ids: list):
        pass

    @abstractmethod
    def delete_all(self):
        pass

    @abstractmethod
    def count_by_query(self, query: dict):
        pass

    @abstractmethod
    def find_recent(self, limit: int = 50):
        pass

    @abstractmethod
    def get_paginated(self, page=1, per_page=10, order=None, search: str = ""):
        pass
