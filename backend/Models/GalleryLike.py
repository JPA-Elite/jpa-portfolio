from bson import ObjectId

class GalleryLike:
    def __init__(self, gallery_id, ip_address, like=True, _id=None):
        self._id = str(_id) if isinstance(_id, ObjectId) else _id
        self.gallery_id = str(gallery_id)
        self.ip_address = ip_address
        self.like = bool(like)

    def to_dict(self):
        """Convert GalleryLike object to a dictionary for MongoDB storage."""
        data = {
            "gallery_id": self.gallery_id,
            "ip_address": self.ip_address,
            "like": self.like
        }
        if self._id:
            data["_id"] = self._id
        return data

    @staticmethod
    def from_dict(data):
        """Create a GalleryLike object from a MongoDB document."""
        _id = data.get("_id")
        if isinstance(_id, dict) and "$oid" in _id:
            _id = str(_id["$oid"])

        return GalleryLike(
            gallery_id=str(data.get("gallery_id")),
            ip_address=data.get("ip_address"),
            like=data.get("like", True),
            _id=_id
        )
