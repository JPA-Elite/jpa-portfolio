from backend.Repositories.Interfaces.IVlogCommentRepository import IVlogCommentRepository
from backend.Models.VlogComment import VlogComment
from backend.utils import num_to_alpha_lower

class VlogCommentService:
    def __init__(self, repository: IVlogCommentRepository):
        self.repository = repository

    def count_comments_by_vlog(self, vlog_id: str):
        return self.repository.count_comments_by_vlog(vlog_id)

    def get_comments(self, vlog_id: str, ip_address: str = None, page: int = 1, limit: int = 10):
        comments_data = self.repository.find__paginate_comments_by_vlog(vlog_id, page, limit)
        total = self.repository.count_comments_by_vlog(vlog_id)
        comments = []

        # Normalize IP address: take only the first valid one
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        for c in comments_data:
            comment = VlogComment.from_dict(c)
            data = comment.to_dict()

            # Convert author_name to readable form
            if "author_name" in data:
                author_name = data.get("author_name", "").replace(".", "")
                data["author_name"] = num_to_alpha_lower(author_name)

            # Check if current user already liked the comment
            if ip_address:
                liked_ips = data.get("liked_ips") or []
                data["is_liked"] = any(
                    ip_address.strip() == ip.strip() for ip in liked_ips
                )

            comments.append(data)

        return comments, total


    def add_comment(self, vlog_id: str, ip_address: str, text: str):
        # Handle cases like "127.0.0.1, 12.1.1.1, 13.9.9.1"
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()  # take first IP only

        author_name = f"user_{ip_address}"
        comment = VlogComment(
            vlog_id=vlog_id,
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
