from abc import ABC, abstractmethod


class IMusicLikeRepository(ABC):
    @abstractmethod
    def get_likes_count(self, music_id: str, is_like: bool = True):
        pass

    @abstractmethod
    def get_dislikes_count(self, music_id: str):
        pass

    @abstractmethod
    def get_likes_counts_by_ids(self, music_ids: list[str], is_like: bool = True):
        pass

    @abstractmethod
    def get_user_vote(self, music_id: str, ip_address: str):
        pass

    @abstractmethod
    def add_vote(self, vote):
        pass

    @abstractmethod
    def update_vote(self, vote):
        pass

    @abstractmethod
    def delete_vote(self, music_id: str, ip_address: str):
        pass
