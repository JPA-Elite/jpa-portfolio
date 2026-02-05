import os
from typing import Any

from dotenv import load_dotenv  # type: ignore
from pymongo import MongoClient  # type: ignore

from backend.Repositories.Interfaces.IBaseRepository import IBaseRepository

load_dotenv()


class BaseRepository(IBaseRepository):
    def __init__(self, collection_name: str):
        self.client, self.db, self.collection = self.get_mongo_client(collection_name)

    def get_mongo_client(self, collection_name: str):
        """
        Create a MongoDB client using the URI and DB name from .env.
        The collection name is passed in explicitly by the repository.
        """
        mongo_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("MONGO_DB")

        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]

        return client, db, collection

    # -------------------------- centralized CRUD methods --------------------------

    def insert_document(self, data: dict):
        return self.collection.insert_one(data)

    def get_document(self, where: dict, projection: dict | None = None):
        if projection is None:
            return self.collection.find_one(where)
        return self.collection.find_one(where, projection)

    def get_documents(self, where: dict | None = None, projection: dict | None = None):
        query = where or {}

        if projection is None:
            if query:
                return self.collection.find(query)
            return self.collection.find()

        return self.collection.find(query, projection)

    def update_document(self, where: dict, data: dict):
        return self.collection.update_one(where, {"$set": data})

    def update_document_by_id(self, object_id: Any, data: dict):
        return self.update_document({"_id": object_id}, data)

    def delete_document(self, where: dict):
        return self.collection.delete_one(where)

    def delete_document_by_id(self, object_id: Any):
        return self.delete_document({"_id": object_id})

    def annul_document_by_id(self, object_id: Any):
        # Kept as alias for teams using "annul" terminology.
        return self.delete_document_by_id(object_id)

    def count(self, where: dict | None = None):
        return self.collection.count_documents(where or {})
