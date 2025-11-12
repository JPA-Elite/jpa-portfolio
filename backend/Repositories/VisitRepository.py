from Repositories.Interfaces.IVisitRepository import IVisitRepository
from Repositories.BaseRepository import BaseRepository
from datetime import datetime
from config import SortOrder
from constants.db_collections import MongoCollections as mc

class VisitRepository(IVisitRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.VISITORS)  # Call the constructor of the base class

    def get_paginated_documents(self, page, per_page, order: SortOrder):
        # Fetch all documents and convert the timestamp to datetime
        all_documents = list(self.collection.find())
        for doc in all_documents:
            if isinstance(doc.get("timestamp"), str):
                try:
                    # Convert the timestamp string to a datetime object
                    doc["timestamp"] = datetime.strptime(doc["timestamp"], "%m/%d/%Y - %I:%M %p")
                except ValueError:
                    doc["timestamp"] = None  # Handle invalid timestamp formats

        # Sort documents by the datetime timestamp
        sorted_documents = sorted(
            [doc for doc in all_documents if doc["timestamp"] is not None],
            key=lambda x: x["timestamp"],
            reverse=(order == SortOrder.DESC),
        )

        # Paginate the sorted documents
        start = (page - 1) * per_page
        end = start + per_page
        paginated_documents = sorted_documents[start:end]

        # Total document count
        total_docs = len(all_documents)

        return paginated_documents, total_docs

    def delete_system_info_by_id(self, object_id):
        """
        Delete a system info record from the database using _id.
        """
        self.collection.delete_one({"_id": object_id})

    def count_visits(self, where_condition: dict = None):
        """
        Count total visits and separate 'Other' (bot) visits from normal visitors (case-insensitive).

        Returns:
            dict: {
                "visitor_total_count": int,
                "bot_total_count": int
            }
        Example:
            {
                "visitor_total_count": 120,
                "bot_total_count": 15
            }
        """
        if where_condition is None:
            where_condition = {}

        # Case-insensitive filter for 'Other'
        other_filter = {"$regex": "^other$", "$options": "i"}

        # Count where os is not 'Other' (case-insensitive)
        visitor_total_count = self.collection.count_documents({
            **where_condition,
            "os": {"$not": other_filter}
        })

        # Count where os IS 'Other' (case-insensitive)
        bot_total_count = self.collection.count_documents({
            **where_condition,
            "os": other_filter
        })

        return {
            "visitor_total_count": visitor_total_count,
            "bot_total_count": bot_total_count
        }