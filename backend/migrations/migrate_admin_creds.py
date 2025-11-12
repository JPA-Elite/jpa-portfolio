import os
from flask import current_app
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

def migrate_admin_creds(collection_name: str, username: str, password: str, reset: bool = False):
    """Migrate admin credentials into MongoDB (not from JSON)."""
    client = MongoClient(current_app.config["MONGO_URI"])
    db = client[current_app.config["MONGO_DB"]]
    users_collection = db[collection_name]

    if reset:
        users_collection.delete_many({"role": "admin"})
        print("⚠️ Reset mode enabled: old admin accounts deleted.")

    # Check if user already exists
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        print(f"ℹ️ User '{username}' already exists in database. Skipping insert.")
        return

    # Encrypt password before storing
    hashed_password = generate_password_hash(password)

    admin_doc = {
        "username": username,
        "password": hashed_password,  # hashed, not plain
        "role": "admin"
    }

    result = users_collection.insert_one(admin_doc)
    print(f"✅ Inserted admin user '{username}' with ID {result.inserted_id}")
