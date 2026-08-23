from abc import ABC, abstractmethod

from app.configurations import SortOrder
from app.Models.BuiltApp import BuiltApp

class IBuiltAppRepository(ABC):
    @abstractmethod
    def get_built_app_by_id(self, app_id: str):
        pass

    @abstractmethod
    def get_paginated_built_apps(
        self,
        page: int,
        per_page: int,
        order: SortOrder,
        search_query: str = "",
        platform_filter: str = "",
        is_active_filter=None,
    ):
        pass

    @abstractmethod
    def get_active_built_apps(self):
        pass

    @abstractmethod
    def find_active_built_app_by_slug(self, slug: str):
        pass

    @abstractmethod
    def count_built_apps(self):
        pass

    @abstractmethod
    def add_built_app(self, built_app: BuiltApp):
        pass

    @abstractmethod
    def add_many_built_apps(self, built_apps: list[BuiltApp]):
        pass

    @abstractmethod
    def update_built_app(self, app_id: str, built_app: BuiltApp):
        pass

    @abstractmethod
    def delete_built_app(self, app_id: str):
        pass
