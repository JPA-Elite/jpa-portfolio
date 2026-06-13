class Video:
    def __init__(self, id, title, description, file, video_url, tags, _id=None):
        self._id = _id  # MongoDB ObjectId

        # ✅ Handle both int and string UUID
        if isinstance(id, dict) and "$numberInt" in id:   # case from Mongo {"$numberInt":"8"}
            self.id = int(id["$numberInt"])
        elif isinstance(id, str) and id.isdigit():        # numeric string
            self.id = int(id)
        else:
            self.id = id  # UUID string or None

        self.title = title or {}        # dict of translations
        self.description = description or {}  # dict of translations
        self.file = file                # video file path
        self.video_url = video_url
        self.tags = tags or []          # list of tags

    def to_dict(self):
        """Convert the Video object to a dictionary for database storage."""
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "file": self.file,
            "video_url": self.video_url,
            "tags": self.tags,
        }

        if self._id is not None:
            data["_id"] = str(self._id)  # ensure string for JSON

        return data

    @staticmethod
    def from_dict(data):
        """Create a Video object from a MongoDB document."""
        _id = data.get("_id")
        if isinstance(_id, dict) and "$oid" in _id:
            _id = str(_id["$oid"])

        # ✅ Handle both Mongo int and UUID string
        id_val = data.get("id")
        if isinstance(id_val, dict) and "$numberInt" in id_val:
            id_val = int(id_val["$numberInt"])

        return Video(
            _id=_id,
            id=id_val,
            title=data.get("title", {}),
            description=data.get("description", {}),
            file=data.get("file"),
            video_url=data.get("video_url"),
            tags=data.get("tags", []),
        )
