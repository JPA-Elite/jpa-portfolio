from abc import ABC, abstractmethod
from config import SortOrder

class IMusicRepository(ABC):
    @abstractmethod
    def get_paginated_music_list(self, page, per_page, order: SortOrder):
        pass

