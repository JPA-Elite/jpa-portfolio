from flask import request, jsonify
from app.Services.GalleryCommentService import GalleryCommentService
from app.Services.UserDisplayNameService import UserDisplayNameService
from app.Repositories.GalleryCommentRepository import GalleryCommentRepository
from app.Repositories.UserDisplayNameRepository import UserDisplayNameRepository
from app.configurations import HTTPMethod as http
from app.Requests.api.GalleryCommentRequest import GalleryCommentRequest
from app.constants.messages import COMMENT_NOT_FOUND_ERROR, COMMENT_DELETE_FORBIDDEN, COMMENT_DELETE_SUCCESS, COMMENT_DELETE_ALL_SUCCESS

gallery_comment_service = GalleryCommentService(
    repository=GalleryCommentRepository(),
    display_name_service=UserDisplayNameService(repository=UserDisplayNameRepository()),
)

def gallery_comments_route():
    form = GalleryCommentRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    if request.method == http.GET:
        gallery_id = data["gallery_id"]
        page = data["page"]
        limit = data["limit"]
        ip_address = data["ip_address"]
        comments, total = gallery_comment_service.get_comments(gallery_id, ip_address=ip_address, page=page, limit=limit)
        display_name, avatar_url, remaining_changes = gallery_comment_service.get_profile(ip_address)
        return jsonify({
            "comments": comments,
            "total": total,
            "page": page,
            "limit": limit,
            "display_name": display_name,
            "avatar_url": avatar_url,
            "remaining_changes": remaining_changes,
        })

    gallery_id = data["gallery_id"]
    text = data["text"]
    ip_address = data["ip_address"]
    comment_id = gallery_comment_service.add_comment(gallery_id, ip_address, text)
    return jsonify({"status": "success", "comment_id": comment_id})

def gallery_like_comment_route():
    form = GalleryCommentRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    comment_id = data["comment_id"]
    ip_address = data["ip_address"]
    result = gallery_comment_service.toggle_like(comment_id, ip_address)
    if result is None:
        return jsonify({"status": "error", "message": COMMENT_NOT_FOUND_ERROR}), 404

    return jsonify({"status": "success", **result})

def gallery_delete_comment_route(comment_id=None):
    form = GalleryCommentRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    result = gallery_comment_service.delete_comment(data.get("comment_id") or comment_id, data["ip_address"])
    if result is None:
        return jsonify({"status": "error", "message": COMMENT_NOT_FOUND_ERROR}), 404
    if result is False:
        return jsonify({"status": "error", "message": COMMENT_DELETE_FORBIDDEN}), 403

    return jsonify({"status": "success", "message": COMMENT_DELETE_SUCCESS})

def gallery_delete_all_comments_route():
    form = GalleryCommentRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    deleted = gallery_comment_service.delete_all_comments(data["gallery_id"], data["ip_address"])
    return jsonify({"status": "success", "deleted": deleted, "message": COMMENT_DELETE_ALL_SUCCESS})
