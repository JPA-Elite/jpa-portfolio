from backend.Repositories.Interfaces.IVlogLikeRepository import IVlogLikeRepository
from backend.Models.VlogLike import VlogLike

class VlogLikeService:
    def __init__(self, repository: IVlogLikeRepository):
        self.repository = repository

    # -------------------------- Vlog Service Methods -------------------------

    def get_vlog_likes_count_by_id(self, vlog_id: str):
        return self.repository.get_vlog_likes_count_by_id(vlog_id)

    def get_vlog_likes_counts_by_ids(self, vlog_ids: list[str]):
        return self.repository.get_vlog_likes_counts_by_ids(vlog_ids)

    def get_vlog_liked_states_by_ids_and_ip(self, vlog_ids: list[str], ip_address: str):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        return self.repository.get_vlog_liked_states_by_ids_and_ip(vlog_ids, ip_address)

    def get_vlog_likes_by_id_and_ip(self, vlog_id: str, ip_address: str, fields: dict = None):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        result = self.repository.get_vlog_likes_by_id_and_ip(vlog_id, ip_address, fields)
        if not result:
            return None

        return VlogLike.from_dict(result)

    def add_vlog_like(self, data: dict):
        try:
            ip_address = data.get("ip_address")
            if ip_address and "," in ip_address:
                data["ip_address"] = ip_address.split(",")[0].strip()

            vlog = VlogLike.from_dict(data)
            return self.repository.add_vlog_like(vlog)

        except Exception as e:
            raise e

    def toggle_vlog_like(self, vlog_id: str, ip_address: str):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        existing_like = self.repository.get_vlog_likes_by_id_and_ip(vlog_id, ip_address)

        if existing_like:
            vlog_like = VlogLike.from_dict(existing_like)
            new_like_value = not vlog_like.like
            vlog_like.like = new_like_value

            updated = self.repository.update_vlog_like(vlog_like)
            return {
                "_id": vlog_like._id,
                "vlog_id": vlog_like.vlog_id,
                "ip_address": vlog_like.ip_address,
                "like": new_like_value,
                "updated": updated
            }

        new_like = VlogLike(vlog_id=vlog_id, ip_address=ip_address, like=True)
        new_id = self.repository.add_vlog_like(new_like)
        return {
            "_id": new_id,
            "vlog_id": vlog_id,
            "ip_address": ip_address,
            "like": True,
            "created": True
        }

