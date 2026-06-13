class KeyProject:
    def __init__(
        self,
        id,
        title,
        description,
        stack="",
        status="shipped",
        image_url=None,
        demo_url="",
        repo_url="",
        sort_order=0,
        is_active=True,
        slides=None,
        _id=None,
    ):
        self._id = _id

        if isinstance(id, dict) and "$numberInt" in id:
            self.id = int(id["$numberInt"])
        elif isinstance(id, str) and id.isdigit():
            self.id = int(id)
        else:
            self.id = id

        self.title = title or {}
        self.description = description or {}
        self.stack = stack or ""
        self.status = status or "shipped"
        self.image_url = image_url
        self.demo_url = demo_url or ""
        self.repo_url = repo_url or ""
        self.sort_order = int(sort_order or 0)
        self.is_active = bool(is_active)
        self.slides = slides or []

    def to_dict(self):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "stack": self.stack,
            "status": self.status,
            "image_url": self.image_url,
            "demo_url": self.demo_url,
            "repo_url": self.repo_url,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "slides": self.slides,
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

        return KeyProject(
            _id=_id,
            id=id_val,
            title=data.get("title", {}),
            description=data.get("description", {}),
            stack=data.get("stack", ""),
            status=data.get("status", "shipped"),
            image_url=data.get("image_url"),
            demo_url=data.get("demo_url", ""),
            repo_url=data.get("repo_url", ""),
            sort_order=data.get("sort_order", 0),
            is_active=data.get("is_active", True),
            slides=data.get("slides", []),
        )
