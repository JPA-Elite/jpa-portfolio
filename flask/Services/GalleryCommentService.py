from Repositories.Interfaces.IGalleryCommentRepository import IGalleryCommentRepository
from Models.GalleryComment import GalleryComment
from utils import num_to_alpha_lower

class GalleryCommentService:
    def __init__(self, repository: IGalleryCommentRepository):
        self.repository = repository

    def get_comments(self, gallery_id: str, ip_address: str = None):
        comments_data = self.repository.find_comments_by_gallery(gallery_id)
        comments = []

        for c in comments_data:
            comment = GalleryComment.from_dict(c)
            data = comment.to_dict()

            if "author_name" in data:
                author_name = data.get("author_name", "").replace(".", "")
                data["author_name"] = num_to_alpha_lower(author_name)
            if ip_address:
                data["is_liked"] = ip_address in (data.get("liked_ips") or [])

            comments.append(data)

        return comments

    def add_comment(self, gallery_id: str, ip_address: str, text: str):
        author_name = 'user_' + ip_address
        comment = GalleryComment(
            gallery_id=gallery_id,
            author_name=author_name,
            text=text,
            ip_address=ip_address,
            liked_ips=[]
            )
        return self.repository.add_comment(comment)

    def toggle_like(self, comment_id: str, ip_address: str):
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
