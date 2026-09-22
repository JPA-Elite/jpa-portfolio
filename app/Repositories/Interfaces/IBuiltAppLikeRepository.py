from abc import ABC, abstractmethod


class IBuiltAppLikeRepository(ABC):
    @abstractmethod
    def get_likes_count(self, app_id: str, is_like: bool = True):
        pass

    @abstractmethod
    def get_user_vote(self, app_id: str, ip_address: str):
        pass

    @abstractmethod
    def add_vote(self, vote):
        pass

    @abstractmethod
    def update_vote(self, vote):
        pass

    @abstractmethod
    def delete_vote(self, app_id: str, ip_address: str):
        pass
