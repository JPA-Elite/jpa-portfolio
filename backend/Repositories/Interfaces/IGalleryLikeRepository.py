from abc import ABC, abstractmethod

from backend.Models.GalleryLike import GalleryLike


class IGalleryLikeRepository(ABC):
    @abstractmethod
    def get_gallery_likes_count_by_id(self, gallery_id: str):
        pass

    @abstractmethod
    def get_gallery_likes_by_id_and_ip(self, gallery_id: str, ip_address: str, fields: dict = None):
        pass

    @abstractmethod
    def add_gallery_like(self, gallery_like: GalleryLike):
        pass

    @abstractmethod
    def update_gallery_like(self, gallery_like: GalleryLike):
        pass
