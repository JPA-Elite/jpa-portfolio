class Video:
    def __init__(self, id, title, description, file, video_url, tags, _id=None):
        self._id = _id

        if isinstance(id, dict) and "$numberInt" in id:
            self.id = int(id["$numberInt"])
        elif isinstance(id, str) and id.isdigit():
            self.id = int(id)
        else:
            self.id = id

        self.title = title or {}
        self.description = description or {}
        self.file = file()
        self.video_url = video_url
        self.tags = tags or []

    def to_dict(self):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "file": self.file,
            "video_url": self.video_url,
            "tags": self.tags,
        }

        if self._id is not None:
            data["_id"] = str(self._id)

        return data

    @staticmethod
    def from_dict(data):
        _id = data.get("_id")
        if isinstance(_id, dict) and "$oid" in _id:
            _id = str(_id["$oid"])

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
