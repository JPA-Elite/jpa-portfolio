from app.Repositories.Interfaces.IGalleryCommentRepository import IGalleryCommentRepository
from app.Models.GalleryComment import GalleryComment
from app.constants.avatars import DEFAULT_AVATAR_URL
from app.utils import num_to_alpha_lower

class GalleryCommentService:
    def __init__(self, repository: IGalleryCommentRepository, display_name_service=None):
        self.repository = repository
        self.display_name_service = display_name_service

    def count_comments_by_gallery(self, gallery_id: str):
        return self.repository.count_comments_by_gallery(gallery_id)

    def get_comments(self, gallery_id: str, ip_address: str = None, page: int = 1, limit: int = 10):
        comments_data = self.repository.find__paginate_comments_by_gallery(gallery_id, page, limit)
        total = self.repository.count_comments_by_gallery(gallery_id)
        comments = []

        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        profiles_map = {}
        if self.display_name_service:
            comment_ips = [c.get("ip_address") for c in comments_data if c.get("ip_address")]
            profiles_map = self.display_name_service.get_profiles_map(comment_ips)

        for c in comments_data:
            comment = GalleryComment.from_dict(c)
            data = comment.to_dict()
            profile = profiles_map.get(comment.ip_address) or {}

            if "author_name" in data:
                stored_name = profile.get("display_name")
                if stored_name:
                    data["author_name"] = stored_name
                else:
                    author_name = data.get("author_name", "").replace(".", "")
                    data["author_name"] = num_to_alpha_lower(author_name)

            data["avatar_url"] = profile.get("avatar_url") or DEFAULT_AVATAR_URL

            data["is_own"] = bool(ip_address) and ip_address.strip() == str(comment.ip_address or "").strip()

            if ip_address:
                liked_ips = data.get("liked_ips") or []
                data["is_liked"] = any(
                    ip_address.strip() == ip.strip() for ip in liked_ips
                )

            comments.append(data)

        return comments, total

    def get_display_name(self, ip_address: str):
        if not self.display_name_service:
            return None, None
        return self.display_name_service.get_display_name(ip_address)

    def get_profile(self, ip_address: str):
        if not self.display_name_service:
            return None, DEFAULT_AVATAR_URL, None
        return self.display_name_service.get_profile(ip_address)

    def add_comment(self, gallery_id: str, ip_address: str, text: str):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        author_name = f"user_{ip_address}"
        comment = GalleryComment(
            gallery_id=gallery_id,
            author_name=author_name,
            text=text,
            ip_address=ip_address,
            liked_ips=[]
        )
        return self.repository.add_comment(comment)

    def toggle_like(self, comment_id: str, ip_address: str):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        comment = self.repository.find_by_id(comment_id)
        if not comment:
            return None
        liked_ips = comment.get("liked_ips", [])
        if ip_address in liked_ips:
            liked_ips.remove(ip_address)
            liked = False
        else:
            liked_ips.append(ip_address)
            liked = True
        comment["liked_ips"] = liked_ips
        self.repository.update_comment(comment)
        return {"liked": liked, "like_count": len(liked_ips)}

    def delete_comment(self, comment_id: str, ip_address: str):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        comment = self.repository.find_by_id(comment_id)
        if not comment:
            return None
        if str(comment.get("ip_address") or "").strip() != ip_address:
            return False
        self.repository.delete_by_id(comment_id)
        return True

    def delete_all_comments(self, gallery_id: str, ip_address: str):
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()
        return self.repository.delete_all_by_content_and_ip("gallery_id", gallery_id, ip_address)

