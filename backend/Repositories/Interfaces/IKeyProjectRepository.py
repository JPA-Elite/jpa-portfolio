from abc import ABC, abstractmethod

from backend.configurations import SortOrder
from backend.Models.KeyProject import KeyProject


class IKeyProjectRepository(ABC):
    @abstractmethod
    def get_key_project_by_id(self, project_id: str):
        pass

    @abstractmethod
    def get_paginated_key_projects(
        self,
        page: int,
        per_page: int,
        order: SortOrder,
        search_query: str = "",
        status_filter: str = "",
        is_active_filter=None,
    ):
        pass

    @abstractmethod
    def get_active_key_projects(self):
        pass

    @abstractmethod
    def count_key_projects(self):
        pass

    @abstractmethod
    def add_key_project(self, key_project: KeyProject):
        pass

    @abstractmethod
    def add_many_key_projects(self, key_projects: list[KeyProject]):
        pass

    @abstractmethod
    def update_key_project(self, project_id: str, key_project: KeyProject):
        pass

    @abstractmethod
    def delete_key_project(self, project_id: str):
        pass
