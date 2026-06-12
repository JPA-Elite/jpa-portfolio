from backend.Repositories.MusicLikeRepository import MusicLikeRepository
from backend.Models.MusicLike import MusicLike

class MusicLikeService:
    def __init__(self, repository: MusicLikeRepository):
        self.repository = repository

    def get_likes_count(self, music_id: str):
        return self.repository.get_likes_count(music_id, is_like=True)

    def get_dislikes_count(self, music_id: str):
        return self.repository.get_likes_count(music_id, is_like=False)

    def get_likes_counts_by_ids(self, music_ids: list[str]):
        return self.repository.get_likes_counts_by_ids(music_ids, is_like=True)

    def get_dislikes_counts_by_ids(self, music_ids: list[str]):
        return self.repository.get_likes_counts_by_ids(music_ids, is_like=False)

    def get_user_vote(self, music_id: str, ip_address: str):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()
        return self.repository.get_user_vote(music_id, ip_address)

    def toggle_vote(self, music_id: str, ip_address: str, is_like: bool):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        existing = self.repository.get_user_vote(music_id, ip_address)

        if existing:
            vote = MusicLike.from_dict(existing)
            if vote.is_like == is_like:
                self.repository.delete_vote(music_id, ip_address)
                return {"action": "removed", "is_like": is_like}
            vote.is_like = is_like
            self.repository.update_vote(vote)
            return {"action": "switched", "is_like": is_like}

        new_vote = MusicLike(music_id=music_id, ip_address=ip_address, is_like=is_like)
        self.repository.add_vote(new_vote)
        return {"action": "added", "is_like": is_like}
