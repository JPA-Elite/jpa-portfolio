from abc import ABC, abstractmethod
from Models.GalleryComment import GalleryComment

class IGalleryCommentRepository(ABC):
    @abstractmethod
    def find_comments_by_gallery(self, gallery_id: str):
        pass

    @abstractmethod
    def add_comment(self, comment: GalleryComment):
        pass

    @abstractmethod
    def find_by_id(self, comment_id: str):
        pass

    @abstractmethod
    def update_comment(self, comment: GalleryComment):
        pass