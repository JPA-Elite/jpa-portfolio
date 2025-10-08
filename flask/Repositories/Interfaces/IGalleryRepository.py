from abc import ABC, abstractmethod
from config import SortOrder
from Models import Music

class IGalleryRepository(ABC):
    @abstractmethod
    def get_gallery_by_id(self, gallery_id: str):
        pass

    @abstractmethod
    def get_paginated_gallery_list(self, page, per_page, order: SortOrder):
        pass

    @abstractmethod
    def add_gallery(self, gallery: Music):
        pass

    @abstractmethod
    def update_gallery(self, gallery_id: str, gallery: Music):
        pass

    @abstractmethod
    def delete_gallery(self, gallery_id: str):
        pass
