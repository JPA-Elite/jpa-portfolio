from abc import ABC, abstractmethod
from app.configurations import SortOrder

class IVisitRepository(ABC):
    @abstractmethod
    def get_paginated_documents(self, page, per_page, order: SortOrder, search: str = ""):
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

    @abstractmethod
    def get_visit_type_counts(self):
        pass

    @abstractmethod
    def find_all_image_captures(self):
        pass

    @abstractmethod
    def get_device_breakdown(self, max_slices: int = 6):
        pass

