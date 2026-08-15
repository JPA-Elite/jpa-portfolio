from abc import ABC, abstractmethod
from app.Models.VlogComment import VlogComment

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

    @abstractmethod
    def delete_by_id(self, comment_id: str):
        pass

    @abstractmethod
    def delete_all_by_content_and_ip(self, content_key: str, content_id: str, ip_address: str):
        pass