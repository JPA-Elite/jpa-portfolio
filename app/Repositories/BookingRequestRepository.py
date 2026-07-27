import re
from bson import ObjectId, errors as bson_errors
from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.Interfaces.IBookingRequestRepository import IBookingRequestRepository
from app.constants.db_collections import MongoCollections as mc
from app.configurations import SortOrder

class BookingRequestRepository(IBookingRequestRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.BOOKING_REQUESTS)

    def insert_booking(self, data: dict):
        return self.insert_one(data)

    def find_by_id(self, booking_id: str):
        try:
            query = {"_id": ObjectId(booking_id)}
        except bson_errors.InvalidId:
            query = {"_id": booking_id}
        return self.find_one(query)

    def get_paginated_list(self, page, per_page, order, search_query=""):
        sort_order = -1 if order == SortOrder.DESC else 1
        query = {}
        if search_query:
            escaped = re.escape(search_query.strip())
            or_filters = [
                {"name": {"$regex": escaped, "$options": "i"}},
                {"email": {"$regex": escaped, "$options": "i"}},
            ]
            query = {"$or": or_filters}
        data = self.find(query, sort=[("created_at", sort_order)], skip=(page-1)*per_page, limit=per_page)
        total = self.count_documents(query)
        return data, total

    def delete_booking(self, booking_id: str):
        try:
            query = {"_id": ObjectId(booking_id)}
        except bson_errors.InvalidId:
            query = {"_id": booking_id}
        result = self.delete_one(query)
        return result.deleted_count > 0

    def count_by_ip_in_window(self, ip_address: str, since: float):
        from datetime import datetime
        since_dt = datetime.utcfromtimestamp(since)
        return self.count_documents({
            "ip_address": ip_address,
            "created_at": {"$gte": since_dt},
        })
