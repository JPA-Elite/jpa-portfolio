from abc import ABC, abstractmethod


class IActivityLogRepository(ABC):
    @abstractmethod
    def insert(self, entry: dict):
        pass
