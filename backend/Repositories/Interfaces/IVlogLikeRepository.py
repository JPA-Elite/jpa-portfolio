from abc import ABC, abstractmethod

from backend.Models.VlogLike import VlogLike


class IVlogLikeRepository(ABC):
    @abstractmethod
    def get_vlog_likes_count_by_id(self, vlog_id: str):
        pass

    @abstractmethod
    def get_vlog_likes_by_id_and_ip(self, vlog_id: str, ip_address: str, fields: dict = None):
        pass

    @abstractmethod
    def add_vlog_like(self, vlog_like: VlogLike):
        pass

    @abstractmethod
    def update_vlog_like(self, vlog_like: VlogLike):
        pass
