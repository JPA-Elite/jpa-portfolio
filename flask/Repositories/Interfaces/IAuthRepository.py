from abc import ABC, abstractmethod

class IAuthRepository(ABC):
    @abstractmethod
    def find_by_username(self, username: str):
        pass