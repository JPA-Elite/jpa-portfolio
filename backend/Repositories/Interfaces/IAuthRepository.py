from abc import ABC, abstractmethod

class IAuthRepository(ABC):
    @abstractmethod
    def find_by_username(self, username: str):
        pass

    @abstractmethod
    def find_by_id(self, id):
        pass

    @abstractmethod
    def update_user(self, id, data: dict):
        pass