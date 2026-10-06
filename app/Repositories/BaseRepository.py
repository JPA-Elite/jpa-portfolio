from dotenv import load_dotenv
from pymongo import MongoClient
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
import os
import threading

load_dotenv()

_shared_clients: Dict[str, Any] = {}
_shared_clients_lock = threading.Lock()

class BaseRepository:
    def __init__(self, collection_name: str):
        self.client, self.db, self.collection = self.get_mongo_client(collection_name)

    def get_mongo_client(self, collection_name: str):
        mongo_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("MONGO_DB")
        cache_key = f"{mongo_uri}||{db_name}"

        with _shared_clients_lock:
            client = _shared_clients.get(cache_key)
            if client is None:
                client = MongoClient(
                    mongo_uri,
                    maxPoolSize=20,
                    minPoolSize=1,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=3000,
                    socketTimeoutMS=10000,
                    retryWrites=True,
                )
                _shared_clients[cache_key] = client

        db = client[db_name]
        collection = db[collection_name]

        return client, db, collection

    # ----------------------------
    # Centralized Mongo operations
    # ----------------------------

    def find(
        self,
        filter: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Tuple[str, int]]] = None,
        skip: int = 0,
        limit: int = 0,
    ) -> List[Dict[str, Any]]:
        filter = filter or {}
        cursor = self.collection.find(filter, projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def find_one(
        self,
        filter: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        return self.collection.find_one(filter, projection)

    def count_documents(self, filter: Dict[str, Any]) -> int:
        return self.collection.count_documents(filter)

    def insert_one(self, document: Dict[str, Any]) -> Any:
        return self.collection.insert_one(document)

    def insert_many(self, documents: Iterable[Dict[str, Any]]) -> Any:
        return self.collection.insert_many(list(documents))

    def update_one(
        self,
        filter: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
    ) -> Any:
        return self.collection.update_one(filter, update, upsert=upsert)

    def update_many(
        self,
        filter: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
    ) -> Any:
        return self.collection.update_many(filter, update, upsert=upsert)

    def delete_one(self, filter: Dict[str, Any]) -> Any:
        return self.collection.delete_one(filter)

    def delete_many(self, filter: Dict[str, Any]) -> Any:
        return self.collection.delete_many(filter)

    def aggregate(self, pipeline: List[Dict[str, Any]], allowDiskUse: bool = False) -> List[Dict[str, Any]]:
        return list(self.collection.aggregate(pipeline, allowDiskUse=allowDiskUse))
