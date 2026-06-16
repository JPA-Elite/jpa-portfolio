from bson import ObjectId
from datetime import datetime


class GalleryComment:
    def __init__(self, gallery_id, author_name, text, ip_address, liked_ips=None, _id=None, created_at=None):
        self._id = _id

        if isinstance(id, dict) and "$numberInt" in id:
            self.id = int(id["$numberInt"])
        elif isinstance(id, str) and id.isdigit():
            self.id = int(id)
        else:
            self.id = id

        self.gallery_id = gallery_id
        self.author_name = author_name
        self.text = text
        self.ip_address = ip_address
        self.liked_ips = liked_ips if liked_ips is not None else []
        self.created_at = created_at if created_at else datetime.utcnow()

    def to_dict(self):
        data = {
            "gallery_id": self.gallery_id,
            "author_name": self.author_name,
            "text": self.text,
            "ip_address": self.ip_address,
            "liked_ips": self.liked_ips,
            "created_at": self.created_at,
        }

        if self._id is not None:
            data["_id"] = str(self._id)

        return data

    @staticmethod
    def from_dict(data):
        if not data:
            return None

        _id = data.get("_id")
        if isinstance(_id, dict) and "$oid" in _id:
            _id = ObjectId(_id["$oid"])
        elif isinstance(_id, str):
            _id = ObjectId(_id) if ObjectId.is_valid(_id) else _id

        return GalleryComment(
            gallery_id=data.get("gallery_id"),
            author_name=data.get("author_name"),
            text=data.get("text"),
            ip_address=data.get("ip_address"),
            liked_ips=data.get("liked_ips", []),
            _id=_id,
            created_at=data.get("created_at"),
        )
