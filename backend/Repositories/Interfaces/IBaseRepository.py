from abc import ABC, abstractmethod
from typing import Any


class IBaseRepository(ABC):
    @abstractmethod
    def insert_document(self, data: dict):
        pass

    @abstractmethod
    def get_document(self, where: dict, projection: dict | None = None):
        pass

    @abstractmethod
    def get_documents(self, where: dict | None = None, projection: dict | None = None):
        pass

    @abstractmethod
    def update_document(self, where: dict, data: dict):
        pass

    @abstractmethod
    def update_document_by_id(self, object_id: Any, data: dict):
        pass

    @abstractmethod
    def delete_document(self, where: dict):
        pass

    @abstractmethod
    def delete_document_by_id(self, object_id: Any):
        pass

    @abstractmethod
    def annul_document_by_id(self, object_id: Any):
        """Alias of delete-by-id for compatibility with 'annul' naming."""
        pass

    @abstractmethod
    def count(self, where: dict | None = None):
        pass
