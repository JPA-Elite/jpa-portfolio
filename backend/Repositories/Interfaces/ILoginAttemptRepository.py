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

    @abstractmethod
    def get_login_attempt_by_id(self, login_attempt_id: str):
        pass

    @abstractmethod
    def get_paginated_login_attempt_list(self, page: int, per_page: int, order, search_query: str = ""):
        pass

    @abstractmethod
    def delete_login_attempt(self, login_attempt_id: str):
        pass
