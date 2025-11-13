from backend.Repositories.Interfaces.IGalleryLikeRepository import IGalleryLikeRepository
from backend.Models.GalleryLike import GalleryLike

class GalleryLikeService:
    def __init__(self, repository: IGalleryLikeRepository):
        self.repository = repository

    # -------------------------- Gallery Service Methods -------------------------

    def get_gallery_likes_count_by_id(self, gallery_id: str):
        return self.repository.get_gallery_likes_count_by_id(gallery_id)


    def get_gallery_likes_by_id_and_ip(self, gallery_id: str, ip_address: str, fields: dict = None):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        result = self.repository.get_gallery_likes_by_id_and_ip(gallery_id, ip_address, fields)
        if not result:
            return None

        return GalleryLike.from_dict(result)


    def add_gallery_like(self, data: dict):
        try:
            # Normalize IP address (only take the first one if multiple exist)
            ip_address = data.get("ip_address")
            if ip_address and "," in ip_address:
                data["ip_address"] = ip_address.split(",")[0].strip()

            gallery = GalleryLike.from_dict(data)
            return self.repository.add_gallery_like(gallery)

        except Exception as e:
            raise e


    def toggle_gallery_like(self, gallery_id: str, ip_address: str):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        existing_like = self.repository.get_gallery_likes_by_id_and_ip(gallery_id, ip_address)

        if existing_like:
            gallery_like = GalleryLike.from_dict(existing_like)
            # Flip the like value
            new_like_value = not gallery_like.like
            gallery_like.like = new_like_value

            updated = self.repository.update_gallery_like(gallery_like)
            return {
                "_id": gallery_like._id,
                "gallery_id": gallery_like.gallery_id,
                "ip_address": gallery_like.ip_address,
                "like": new_like_value,
                "updated": updated
            }

        # If not foundages → create new like = True
        new_like = GalleryLike(gallery_id=gallery_id, ip_address=ip_address, like=True)
        new_id = self.repository.add_gallery_like(new_like)
        return {
            "_id": new_id,
            "gallery_id": gallery_id,
            "ip_address": ip_address,
            "like": True,
            "created": True
        }