from app.Repositories.Interfaces.IBuiltAppLikeRepository import IBuiltAppLikeRepository
from app.Models.BuiltAppLike import BuiltAppLike

class BuiltAppLikeService:
    def __init__(self, repository: IBuiltAppLikeRepository):
        self.repository = repository

    def get_likes_count(self, app_id: str):
        return self.repository.get_likes_count(app_id, is_like=True)

    def get_dislikes_count(self, app_id: str):
        return self.repository.get_likes_count(app_id, is_like=False)

    def get_user_vote(self, app_id: str, ip_address: str):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()
        return self.repository.get_user_vote(app_id, ip_address)

    def toggle_vote(self, app_id: str, ip_address: str, is_like: bool):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        existing = self.repository.get_user_vote(app_id, ip_address)

        if existing:
            vote = BuiltAppLike.from_dict(existing)
            if vote.is_like == is_like:
                self.repository.delete_vote(app_id, ip_address)
                return {"action": "removed", "is_like": is_like}
            vote.is_like = is_like
            self.repository.update_vote(vote)
            return {"action": "switched", "is_like": is_like}

        new_vote = BuiltAppLike(app_id=app_id, ip_address=ip_address, is_like=is_like)
        self.repository.add_vote(new_vote)
        return {"action": "added", "is_like": is_like}
