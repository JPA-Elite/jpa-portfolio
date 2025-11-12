import json
import os
from flask import current_app
from pymongo import MongoClient

def migrate_json_data(file_name: str, collection_name: str, reset: bool = False):
    """Migrate data file into MongoDB (sorted by ascending ID)."""
    client = MongoClient(current_app.config["MONGO_URI"])
    db = client[current_app.config["MONGO_DB"]]
    data_collection = db[collection_name]

    # Build path relative to Flask app root
    json_file_path = os.path.join(current_app.root_path, "static", "json", file_name)

    # Load JSON file
    with open(json_file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    if not isinstance(json_data, list):
        raise ValueError("json file must contain a list of objects")

    # Sort data ascending by id
    json_data.sort(key=lambda x: x.get("id", 0))

    # Reset (clear old docs) if requested
    if reset:
        data_collection.delete_many({})
        print("⚠️ Reset mode enabled: old documents deleted.")

    # Insert into MongoDB
    result = data_collection.insert_many(json_data)
    print(f"✅ Inserted {len(result.inserted_ids)} documents into '{collection_name}' collection (sorted ascending by id).")
