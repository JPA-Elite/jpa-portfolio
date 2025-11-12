from abc import ABC, abstractmethod
from config import SortOrder
from Models import Music

class IVideoRepository(ABC):
    @abstractmethod
    def get_video_by_id(self, video_id: str):
        pass

    @abstractmethod
    def get_paginated_video_list(self, page, per_page, order: SortOrder):
        pass

    @abstractmethod
    def add_video(self, video: Music):
        pass

    @abstractmethod
    def update_video(self, video_id: str, video: Music):
        pass

    @abstractmethod
    def delete_video(self, video_id: str):
        pass

    @abstractmethod
    def search_video_paginated(self, search_query: str = "", tags: list[str] = None, locale: str = "en", page: int = 1, per_page: int = 10, order: SortOrder = SortOrder.DESC):
        pass

    @abstractmethod
    def get_all_tags(self, limit: int = 50):
        pass