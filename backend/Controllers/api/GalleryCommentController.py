from flask import request, jsonify
from Services.GalleryCommentService import GalleryCommentService
from Repositories.GalleryCommentRepository import GalleryCommentRepository
from configurations import HTTPMethod as http
from constants.messages import COMMENT_NOT_FOUND_ERROR

# Initialize Services
gallery_comment_service = GalleryCommentService(repository=GalleryCommentRepository())

# Gallery Comment Controller
def gallery_comments_route():
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if request.method == http.GET:
        gallery_id = request.args.get("gallery_id")
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        comments, total = gallery_comment_service.get_comments(gallery_id, ip_address=ip_address, page=page, limit=limit)
        return jsonify({
            "comments": comments,
            "total": total,
            "page": page,
            "limit": limit
        })

    # POST new comment
    data = request.json
    gallery_id = data.get("gallery_id")
    text = data.get("text")
    comment_id = gallery_comment_service.add_comment(gallery_id, ip_address, text)
    return jsonify({"status": "success", "comment_id": comment_id})


def gallery_like_comment_route():
    data = request.json
    comment_id = data.get("comment_id")
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    result = gallery_comment_service.toggle_like(comment_id, ip_address)
    if result is None:
        return jsonify({"status": "error", "message": COMMENT_NOT_FOUND_ERROR}), 404

    return jsonify({"status": "success", **result})