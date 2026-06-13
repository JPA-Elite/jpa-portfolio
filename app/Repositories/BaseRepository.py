from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()

class BaseRepository:
    def __init__(self, collection_name: str):
        self.client, self.db, self.collection = self.get_mongo_client(collection_name)

    def get_mongo_client(self, collection_name: str):
        mongo_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("MONGO_DB")

        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]

        return client, db, collection

