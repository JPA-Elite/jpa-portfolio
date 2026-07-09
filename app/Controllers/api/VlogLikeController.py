from flask import request, jsonify
from app.Services.VlogLikeService import VlogLikeService
from app.Repositories.VlogLikeRepository import VlogLikeRepository
from app.Services.VlogCommentService import VlogCommentService
from app.Repositories.VlogCommentRepository import VlogCommentRepository
from app.Requests.api.VlogLikeRequest import VlogLikeRequest
from app.constants.messages import VIDEO_LIKE_TOGGLE_MSG
from app.utils import clear_cache_by_prefix

# Initialize Services
vlog_like_service = VlogLikeService(repository=VlogLikeRepository())
vlog_comment_service = VlogCommentService(repository=VlogCommentRepository())

# Vlog Like Controller
def get_vlog_likes_count_route():
    form = VlogLikeRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    vlog_id = data["vlog_id"]
    client_ip = data["client_ip"]

    comment_counts = vlog_comment_service.count_comments_by_vlog(vlog_id)
    like_counts = vlog_like_service.get_vlog_likes_count_by_id(vlog_id)
    like_doc = vlog_like_service.get_vlog_likes_by_id_and_ip(vlog_id, client_ip, {"like": 1})
    is_liked = like_doc.to_dict() if like_doc else False

    return jsonify({
            "comment_counts": comment_counts,
            "like_counts": like_counts,
            "is_liked": is_liked['like'] if is_liked else False
        }), 200

def get_vlog_likes_counts_batch_route():
    form = VlogLikeRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    vlog_ids = data["vlog_ids"]
    client_ip = data["client_ip"]

    if not vlog_ids:
        return jsonify({"items": {}}), 200

    comment_counts_by_vlog = vlog_comment_service.count_comments_by_vlog_ids(vlog_ids)
    like_counts_by_vlog = vlog_like_service.get_vlog_likes_counts_by_ids(vlog_ids)
    liked_states_by_vlog = vlog_like_service.get_vlog_liked_states_by_ids_and_ip(vlog_ids, client_ip)

    items = {}
    for vlog_id in vlog_ids:
        items[vlog_id] = {
            "comment_counts": comment_counts_by_vlog.get(vlog_id, 0),
            "like_counts": like_counts_by_vlog.get(vlog_id, 0),
            "is_liked": liked_states_by_vlog.get(vlog_id, False)
        }

    return jsonify({"items": items}), 200

def add_vlog_like_route():
    form = VlogLikeRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    vlog_id = data["vlog_id"]
    client_ip = data["client_ip"]

    try:
        result = vlog_like_service.toggle_vlog_like(
            vlog_id=vlog_id,
            ip_address=client_ip
        )

        clear_cache_by_prefix("vlog_")
        return jsonify({
            "message": VIDEO_LIKE_TOGGLE_MSG,
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

