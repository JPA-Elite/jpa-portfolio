from flask import request, jsonify
from app.Services.VlogCommentService import VlogCommentService
from app.Repositories.VlogCommentRepository import VlogCommentRepository
from app.configurations import HTTPMethod as http
from app.Requests.api.VlogCommentRequest import VlogCommentRequest
from app.constants.messages import COMMENT_NOT_FOUND_ERROR

# Initialize Services
vlog_comment_service = VlogCommentService(repository=VlogCommentRepository())

# Vlog Comment Controller
def vlog_comments_route():
    form = VlogCommentRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    if request.method == http.GET:
        vlog_id = data["vlog_id"]
        page = data["page"]
        limit = data["limit"]
        ip_address = data["ip_address"]
        comments, total = vlog_comment_service.get_comments(vlog_id, ip_address=ip_address, page=page, limit=limit)
        return jsonify({
            "comments": comments,
            "total": total,
            "page": page,
            "limit": limit
        })

    vlog_id = data["vlog_id"]
    text = data["text"]
    ip_address = data["ip_address"]
    comment_id = vlog_comment_service.add_comment(vlog_id, ip_address, text)
    return jsonify({"status": "success", "comment_id": comment_id})

def vlog_like_comment_route():
    form = VlogCommentRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    comment_id = data["comment_id"]
    ip_address = data["ip_address"]
    result = vlog_comment_service.toggle_like(comment_id, ip_address)
    if result is None:
        return jsonify({"status": "error", "message": COMMENT_NOT_FOUND_ERROR}), 404

    return jsonify({"status": "success", **result})
