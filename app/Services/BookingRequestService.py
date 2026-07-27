from datetime import timedelta
from app.Repositories.Interfaces.IBookingRequestRepository import IBookingRequestRepository
from app.Models.BookingRequest import BookingRequest

class BookingRequestService:
    def __init__(self, repository: IBookingRequestRepository):
        self.repository = repository

    def get_paginated_list(self, page, per_page, order, search_query=""):
        data, total = self.repository.get_paginated_list(page, per_page, order, search_query)
        items = []
        for doc in data:
            item = BookingRequest.from_dict(doc)
            created = item.created_at
            if created:
                ph_time = created + timedelta(hours=8)
                item._display_created = ph_time.strftime("%Y-%m-%d %I:%M %p")
            else:
                item._display_created = ""
            items.append(item)
        return items, total

    def get_by_id(self, booking_id: str):
        doc = self.repository.find_by_id(booking_id)
        if not doc:
            return None
        return BookingRequest.from_dict(doc)

    def delete_booking(self, booking_id: str):
        existing = self.get_by_id(booking_id)
        if not existing:
            return False
        return self.repository.delete_booking(booking_id)
