from abc import ABC, abstractmethod
from app.configurations import SortOrder
from app.Models import Music

class IMusicRepository(ABC):
    @abstractmethod
    def get_music_by_id(self, music_id: str):
        pass

    @abstractmethod
    def get_music_by_url(self, music_url: str):
        pass

    @abstractmethod
    def get_paginated_music_list(self, page, per_page, order: SortOrder, search_query: str = ""):
        pass

    @abstractmethod
    def add_music(self, music: Music):
        pass

    @abstractmethod
    def update_music(self, music_id: str, music: Music):
        pass

    @abstractmethod
    def delete_music(self, music_id: str):
        pass

    @abstractmethod
    def get_total_music_count(self) -> int:
        pass
