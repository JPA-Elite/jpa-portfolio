from flask import request, jsonify
from backend.Services.VlogCommentService import VlogCommentService
from backend.Repositories.VlogCommentRepository import VlogCommentRepository
from backend.configurations import HTTPMethod as http
from backend.constants.messages import COMMENT_NOT_FOUND_ERROR

# Initialize Services
vlog_comment_service = VlogCommentService(repository=VlogCommentRepository())

# Vlog Comment Controller
def vlog_comments_route():
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if request.method == http.GET:
        vlog_id = request.args.get("vlog_id")
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        comments, total = vlog_comment_service.get_comments(vlog_id, ip_address=ip_address, page=page, limit=limit)
        return jsonify({
            "comments": comments,
            "total": total,
            "page": page,
            "limit": limit
        })

    data = request.json
    vlog_id = data.get("vlog_id")
    text = data.get("text")
    comment_id = vlog_comment_service.add_comment(vlog_id, ip_address, text)
    return jsonify({"status": "success", "comment_id": comment_id})

def vlog_like_comment_route():
    data = request.json
    comment_id = data.get("comment_id")
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    result = vlog_comment_service.toggle_like(comment_id, ip_address)
    if result is None:
        return jsonify({"status": "error", "message": COMMENT_NOT_FOUND_ERROR}), 404

    return jsonify({"status": "success", **result})
