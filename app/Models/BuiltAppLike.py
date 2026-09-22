class BuiltAppLike:
    def __init__(self, app_id, ip_address, is_like=True, _id=None):
        self._id = str(_id) if _id and not isinstance(_id, str) else _id
        self.app_id = str(app_id)
        self.ip_address = ip_address
        self.is_like = bool(is_like)

    def to_dict(self):
        data = {
            "app_id": self.app_id,
            "ip_address": self.ip_address,
            "is_like": self.is_like
        }
        if self._id:
            data["_id"] = self._id
        return data

    @staticmethod
    def from_dict(data):
        _id = data.get("_id")
        if isinstance(_id, dict) and "$oid" in _id:
            _id = str(_id["$oid"])
        return BuiltAppLike(
            app_id=str(data.get("app_id")),
            ip_address=data.get("ip_address"),
            is_like=data.get("is_like", True),
            _id=_id
        )
