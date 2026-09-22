class BuiltApp:
    def __init__(
        self,
        id,
        slug,
        platform="Mobile",
        version="",
        icon="apps-outline",
        icon_image_url="",
        name=None,
        short_description=None,
        full_description=None,
        snapshots=None,
        download_url="",
        sort_order=0,
        is_active=True,
        _id=None,
    ):
        self._id = _id

        if isinstance(id, dict) and "$numberInt" in id:
            self.id = int(id["$numberInt"])
        elif isinstance(id, str) and id.isdigit():
            self.id = int(id)
        else:
            self.id = id

        self.slug = slug or ""
        self.platform = platform or "Mobile"
        self.version = version or ""
        self.icon = icon or "apps-outline"
        self.icon_image_url = icon_image_url or ""
        self.name = name or {}
        self.short_description = short_description or {}
        self.full_description = full_description or {}
        self.snapshots = snapshots or []
        self.download_url = download_url or ""
        self.sort_order = int(sort_order or 0)
        self.is_active = bool(is_active)

    def to_dict(self):
        data = {
            "id": self.id,
            "slug": self.slug,
            "platform": self.platform,
            "version": self.version,
            "icon": self.icon,
            "icon_image_url": self.icon_image_url,
            "name": self.name,
            "short_description": self.short_description,
            "full_description": self.full_description,
            "snapshots": self.snapshots,
            "download_url": self.download_url,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
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

        return BuiltApp(
            _id=_id,
            id=id_val,
            slug=data.get("slug", ""),
            platform=data.get("platform", "Mobile"),
            version=data.get("version", ""),
            icon=data.get("icon", "apps-outline"),
            icon_image_url=data.get("icon_image_url", ""),
            name=data.get("name", {}),
            short_description=data.get("short_description", {}),
            full_description=data.get("full_description", {}),
            snapshots=data.get("snapshots", []),
            download_url=data.get("download_url", ""),
            sort_order=data.get("sort_order", 0),
            is_active=data.get("is_active", True),
        )
