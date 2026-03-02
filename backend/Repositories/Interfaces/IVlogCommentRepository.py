from abc import ABC, abstractmethod
from Models.VlogComment import VlogComment

class IVlogCommentRepository(ABC):
    @abstractmethod
    def find_comments_by_vlog(self, vlog_id: str):
        pass

    @abstractmethod
    def find__paginate_comments_by_vlog(self, vlog_id: str, page: int, limit: int):
        pass

    @abstractmethod
    def count_comments_by_vlog(self, vlog_id: str):
        pass

    @abstractmethod
    def add_comment(self, comment: VlogComment):
        pass

    @abstractmethod
    def find_by_id(self, comment_id: str):
        pass

    @abstractmethod
    def update_comment(self, comment: VlogComment):
        pass