from Repositories.BaseRepository import BaseRepository
from datetime import datetime
from config import SortOrder
from bson import ObjectId

class VisitRepository(BaseRepository):
    def __init__(self):
        super().__init__()  # Call the constructor of the base class

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