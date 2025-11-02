from abc import ABC, abstractmethod

class ILoginAttemptRepository(ABC):
    @abstractmethod
    def _get_client_ip(self):
        pass

    @abstractmethod
    def get_attempt_info(self):
        pass

    @abstractmethod
    def update_attempt(self, success: bool = False):
        pass