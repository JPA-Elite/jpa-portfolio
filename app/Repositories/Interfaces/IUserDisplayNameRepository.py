from abc import ABC, abstractmethod


class IUserDisplayNameRepository(ABC):
    @abstractmethod
    def find_by_ip(self, ip_address: str):
        pass

    @abstractmethod
    def find_display_names_by_ips(self, ip_addresses: list[str]):
        pass

    @abstractmethod
    def find_profiles_by_ips(self, ip_addresses: list[str]):
        pass

    @abstractmethod
    def upsert_display_name(self, ip_address: str, display_name: str, change_count: int, changed_date: str):
        pass

    @abstractmethod
    def upsert_avatar(self, ip_address: str, avatar_url: str, change_count: int, changed_date: str):
        pass
