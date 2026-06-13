class MusicLike:
    def __init__(self, music_id, ip_address, is_like=True, _id=None):
        self._id = str(_id) if _id and not isinstance(_id, str) else _id
        self.music_id = str(music_id)
        self.ip_address = ip_address
        self.is_like = bool(is_like)

    def to_dict(self):
        data = {
            "music_id": self.music_id,
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
        return MusicLike(
            music_id=str(data.get("music_id")),
            ip_address=data.get("ip_address"),
            is_like=data.get("is_like", True),
            _id=_id
        )
