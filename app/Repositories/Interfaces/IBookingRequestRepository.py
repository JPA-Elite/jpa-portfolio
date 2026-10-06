from abc import ABC, abstractmethod
from app.configurations import SortOrder


class IBookingRequestRepository(ABC):
    @abstractmethod
    def insert_booking(self, data: dict):
        pass

    @abstractmethod
    def find_by_id(self, booking_id: str):
        pass

    @abstractmethod
    def get_paginated_list(self, page, per_page, order, search_query=""):
        pass

    @abstractmethod
    def delete_booking(self, booking_id: str):
        pass

    @abstractmethod
    def delete_all(self):
        pass

    @abstractmethod
    def count_by_ip_in_window(self, ip_address: str, since: float):
        pass
