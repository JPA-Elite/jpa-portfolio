class Gallery:
    def __init__(self, id, title, description, image_url=None, tags=None, _id=None):
        self._id = _id  # MongoDB ObjectId (string)

        # ✅ Handle both Mongo Int and UUID/String IDs
        if isinstance(id, dict) and "$numberInt" in id:
            self.id = int(id["$numberInt"])
        elif isinstance(id, str) and id.isdigit():
            self.id = int(id)
        else:
            self.id = id  # UUID or None

        self.title = title or {}
        self.description = description or {}
        self.image_url = image_url  # Cloudinary / image link
        self.tags = tags or []

    def to_dict(self):
        """Convert Gallery object to a dictionary for MongoDB storage."""
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            # 🔁 Ensure field consistency with DB key
            "image_url": self.image_url,
            "tags": self.tags,
        }

        if self._id is not None:
            data["_id"] = str(self._id)

        return data

    @staticmethod
    def from_dict(data):
        """Create a Gallery object from a MongoDB document."""
        _id = data.get("_id")
        if isinstance(_id, dict) and "$oid" in _id:
            _id = str(_id["$oid"])

        # Handle integer or UUID id
        id_val = data.get("id")
        if isinstance(id_val, dict) and "$numberInt" in id_val:
            id_val = int(id_val["$numberInt"])

        # 🔁 Map `image_url` from DB → `image_url` in model
        image_url = data.get("image_url") or data.get("image_url")

        return Gallery(
            _id=_id,
            id=id_val,
            title=data.get("title", {}),
            description=data.get("description", {}),
            image_url=image_url,
            tags=data.get("tags", []),
        )
