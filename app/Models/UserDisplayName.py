class UserDisplayName:
    def __init__(
        self,
        ip_address="",
        display_name=None,
        avatar_url=None,
        change_count=0,
        changed_date=None,
        avatar_change_count=0,
        avatar_changed_date=None,
        _id=None,
        **extra,
    ):
        self._id = str(_id) if _id is not None else None
        self.ip_address = ip_address or ""
        self.display_name = display_name
        self.avatar_url = avatar_url
        self.change_count = int(change_count or 0)
        self.changed_date = changed_date
        self.avatar_change_count = int(avatar_change_count or 0)
        self.avatar_changed_date = avatar_changed_date
        self.extra = dict(extra or {})

    def to_dict(self):
        data = {
            "ip_address": self.ip_address,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "change_count": self.change_count,
            "changed_date": self.changed_date,
            "avatar_change_count": self.avatar_change_count,
            "avatar_changed_date": self.avatar_changed_date,
        }
        data.update(self.extra)
        if self._id is not None:
            data["_id"] = str(self._id)
        return data

    @staticmethod
    def from_dict(data):
        data = dict(data or {})
        _id = data.pop("_id", None)
        if isinstance(_id, dict) and "$oid" in _id:
            _id = str(_id["$oid"])
        return UserDisplayName(
            ip_address=data.pop("ip_address", ""),
            display_name=data.pop("display_name", None),
            avatar_url=data.pop("avatar_url", None),
            change_count=data.pop("change_count", 0),
            changed_date=data.pop("changed_date", None),
            avatar_change_count=data.pop("avatar_change_count", 0),
            avatar_changed_date=data.pop("avatar_changed_date", None),
            _id=_id,
            **data,
        )
