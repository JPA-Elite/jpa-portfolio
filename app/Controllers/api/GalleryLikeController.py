from flask import request, jsonify
from app.Services.GalleryLikeService import GalleryLikeService
from app.Repositories.GalleryLikeRepository import GalleryLikeRepository
from app.Services.GalleryCommentService import GalleryCommentService
from app.Repositories.GalleryCommentRepository import GalleryCommentRepository
from app.Requests.api.GalleryLikeRequest import GalleryLikeRequest
from app.constants.messages import GALLERY_LIKE_TOGGLE_MSG
from app.utils import clear_cache_by_prefix

# Initialize Services
gallery_like_service = GalleryLikeService(repository=GalleryLikeRepository())
gallery_comment_service = GalleryCommentService(repository=GalleryCommentRepository())

# Gallery Like Controller
def get_gallery_likes_count_route():
    form = GalleryLikeRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    gallery_id = data["gallery_id"]
    client_ip = data["client_ip"]

    comment_counts = gallery_comment_service.count_comments_by_gallery(gallery_id)
    like_counts = gallery_like_service.get_gallery_likes_count_by_id(gallery_id)
    like_doc = gallery_like_service.get_gallery_likes_by_id_and_ip(gallery_id, client_ip, {"like": 1})
    is_liked = like_doc.to_dict() if like_doc else False

    return jsonify({
            "comment_counts": comment_counts,
            "like_counts": like_counts,
            "is_liked": is_liked['like'] if is_liked else False
        }), 200

def get_gallery_likes_counts_batch_route():
    form = GalleryLikeRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    gallery_ids = data["gallery_ids"]
    client_ip = data["client_ip"]

    if not gallery_ids:
        return jsonify({"items": {}}), 200

    items = {}
    for gallery_id in gallery_ids:
        comment_counts = gallery_comment_service.count_comments_by_gallery(gallery_id)
        like_counts = gallery_like_service.get_gallery_likes_count_by_id(gallery_id)
        like_doc = gallery_like_service.get_gallery_likes_by_id_and_ip(
            gallery_id,
            client_ip,
            {"like": 1}
        )
        is_liked = like_doc.to_dict() if like_doc else False

        items[gallery_id] = {
            "comment_counts": comment_counts,
            "like_counts": like_counts,
            "is_liked": is_liked['like'] if is_liked else False
        }

    return jsonify({"items": items}), 200

def add_gallery_like_route():
    form = GalleryLikeRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    gallery_id = data["gallery_id"]
    client_ip = data["client_ip"]

    try:
        result = gallery_like_service.toggle_gallery_like(
            gallery_id=gallery_id,
            ip_address=client_ip
        )

        clear_cache_by_prefix("gallery_")
        return jsonify({
            "message": GALLERY_LIKE_TOGGLE_MSG,
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

