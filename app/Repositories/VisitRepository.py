from app.Repositories.Interfaces.IVisitRepository import IVisitRepository
from app.Repositories.BaseRepository import BaseRepository
from datetime import datetime
from app.configurations import SortOrder
from app.constants.db_collections import MongoCollections as mc

class VisitRepository(IVisitRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VISITORS)

    def get_paginated_documents(self, page, per_page, order: SortOrder):
        all_documents = list(self.collection.find())
        for doc in all_documents:
            if isinstance(doc.get("timestamp"), str):
                try:
                    doc["timestamp"] = datetime.strptime(doc["timestamp"], "%m/%d/%Y - %I:%M %p")
                except ValueError:
                    doc["timestamp"] = None

        sorted_documents = sorted(
            [doc for doc in all_documents if doc["timestamp"] is not None],
            key=lambda x: x["timestamp"],
            reverse=(order == SortOrder.DESC),
        )

        start = (page - 1) * per_page
        end = start + per_page
        paginated_documents = sorted_documents[start:end]

        total_docs = len(all_documents)

        return paginated_documents, total_docs

    def delete_system_info_by_id(self, object_id):
        self.collection.delete_one({"_id": object_id})

    def count_visits(self, where_condition: dict = None):
        if where_condition is None:
            where_condition = {}

        other_filter = {"$regex": "^other$", "$options": "i"}

        visitor_total_count = self.collection.count_documents({
            **where_condition,
            "os": {"$not": other_filter}
        })

        bot_total_count = self.collection.count_documents({
            **where_condition,
            "os": other_filter
        })

        return {
            "visitor_total_count": visitor_total_count,
            "bot_total_count": bot_total_count
        }

    def delete_all_visitors(self) -> bool:

        try:
            delete_many = getattr(self.collection, "delete_many", None)
            if callable(delete_many):
                result = delete_many({})
                _ = getattr(result, "deleted_count", None)
                return True

            if hasattr(self.collection, "delete_all"):
                self.collection.delete_all({})
                return True

            return False
        except Exception:
            return False

