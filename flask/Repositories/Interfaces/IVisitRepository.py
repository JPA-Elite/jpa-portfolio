from abc import ABC, abstractmethod
from config import SortOrder

class IVisitRepository(ABC):
    @abstractmethod
    def get_paginated_documents(self, page, per_page, order: SortOrder):
        pass

    @abstractmethod
    def delete_system_info_by_id(self, object_id):
        pass

