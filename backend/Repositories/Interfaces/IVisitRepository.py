from abc import ABC, abstractmethod
from backend.configurations import SortOrder

class IVisitRepository(ABC):
    @abstractmethod
    def get_paginated_documents(self, page, per_page, order: SortOrder):
        pass

    @abstractmethod
    def delete_system_info_by_id(self, object_id):
        pass

    @abstractmethod
    def count_visits(self, where_condition: dict = None):
        pass

    @abstractmethod
    def delete_all_visitors(self) -> dict:
        pass

