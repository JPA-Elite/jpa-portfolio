from bson import ObjectId

class VlogLike:
    def __init__(self, vlog_id, ip_address, like=True, _id=None):
        self._id = str(_id) if isinstance(_id, ObjectId) else _id
        self.vlog_id = str(vlog_id)
        self.ip_address = ip_address
        self.like = bool(like)

    def to_dict(self):
        data = {
            "vlog_id": self.vlog_id,
            "ip_address": self.ip_address,
            "like": self.like
        }
        if self._id:
            data["_id"] = self._id
        return data

    @staticmethod
    def from_dict(data):
        _id = data.get("_id")
        if isinstance(_id, dict) and "$oid" in _id:
            _id = str(_id["$oid"])

        return VlogLike(
            vlog_id=str(data.get("vlog_id")),
            ip_address=data.get("ip_address"),
            like=data.get("like", True),
            _id=_id
        )
