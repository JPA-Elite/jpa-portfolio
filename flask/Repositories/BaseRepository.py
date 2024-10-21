from dotenv import load_dotenv  # type: ignore
from pymongo import MongoClient  # type: ignore
import os

load_dotenv()


class BaseRepository:
    def __init__(self):
        self.client, self.collection = self.get_mongo_client()

    # database connection
    def get_mongo_client(self):
        """Create a MongoDB client using the URI from the environment variable and return the client, database, and collection."""
        mongo_uri = os.getenv("MONGO_URI")
        client = MongoClient(mongo_uri)

        db = client.get_database(os.getenv("MONGO_DB"))
        portfolio_collection = db.get_collection(os.getenv("MONGO_COLLECTION"))

        return client, portfolio_collection
