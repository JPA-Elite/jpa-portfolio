class ActivityLog:
    def __init__(
        self,
        method="",
        path="",
        status_code=0,
        remote_addr="",
        timestamp="",
        body=None,
        user_id=None,
        user=None,
        _id=None,
        **extra,
    ):
        self._id = str(_id) if _id is not None else None
        self.method = method or ""
        self.path = path or ""
        self.status_code = status_code
        self.remote_addr = remote_addr or ""
        self.timestamp = timestamp or ""
        self.body = body
        self.user_id = user_id
        self.user = user
        self.extra = dict(extra or {})

    def to_dict(self):
        data = {
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "remote_addr": self.remote_addr,
            "timestamp": self.timestamp,
        }
        if self.body is not None:
            data["body"] = self.body
        if self.user_id is not None:
            data["user_id"] = self.user_id
        if self.user is not None:
            data["user"] = self.user
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
        return ActivityLog(
            method=data.pop("method", ""),
            path=data.pop("path", ""),
            status_code=data.pop("status_code", 0),
            remote_addr=data.pop("remote_addr", ""),
            timestamp=data.pop("timestamp", ""),
            body=data.pop("body", None),
            user_id=data.pop("user_id", None),
            user=data.pop("user", None),
            _id=_id,
            **data,
        )
