from flask import request, jsonify
from backend.Services.GalleryLikeService import GalleryLikeService
from backend.Repositories.GalleryLikeRepository import GalleryLikeRepository
from backend.Services.GalleryCommentService import GalleryCommentService
from backend.Repositories.GalleryCommentRepository import GalleryCommentRepository
import json
from backend.constants.messages import GALLERY_LIKE_TOGGLE_MSG
from backend.utils import clear_cache_by_prefix

# Initialize Services
gallery_like_service = GalleryLikeService(repository=GalleryLikeRepository())
gallery_comment_service = GalleryCommentService(repository=GalleryCommentRepository())

# Gallery Like Controller
def get_gallery_likes_count_route():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    gallery_id = request.args.get("gallery_id", "")

    comment_counts = gallery_comment_service.count_comments_by_gallery(gallery_id)
    like_counts = gallery_like_service.get_gallery_likes_count_by_id(gallery_id)
    like_doc = gallery_like_service.get_gallery_likes_by_id_and_ip(gallery_id, client_ip, {"like": 1})
    is_liked = like_doc.to_dict() if like_doc else False

    return jsonify({
            "comment_counts": comment_counts,
            "like_counts": like_counts,
            "is_liked": is_liked['like'] if is_liked else False
        }), 200

def add_gallery_like_route():
    gallery_id = request.form.get("gallery_id")
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if not gallery_id:
        return jsonify({"error": "Missing gallery_id"}), 400

    try:
        # Perform toggle logic (insert or update)
        result = gallery_like_service.toggle_gallery_like(
            gallery_id=json.loads(gallery_id),
            ip_address=client_ip
        )

        clear_cache_by_prefix("gallery_")
        return jsonify({
            "message": GALLERY_LIKE_TOGGLE_MSG,
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
