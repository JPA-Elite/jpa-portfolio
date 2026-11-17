from flask import request
from app.Services.VlogCommentService import VlogCommentService
from app.Services.UserDisplayNameService import UserDisplayNameService
from app.Repositories.VlogCommentRepository import VlogCommentRepository
from app.Repositories.UserDisplayNameRepository import UserDisplayNameRepository
from app.core.configurations import HTTPMethod as http, HTTPStatus as status
from app.core.responses import json_response, status_response
from app.Requests.api.VlogCommentRequest import VlogCommentRequest
from app.constants.messages import COMMENT_NOT_FOUND_ERROR, COMMENT_DELETE_FORBIDDEN, COMMENT_DELETE_SUCCESS, COMMENT_DELETE_ALL_SUCCESS

# Initialize Services
vlog_comment_service = VlogCommentService(
    repository=VlogCommentRepository(),
    display_name_service=UserDisplayNameService(repository=UserDisplayNameRepository()),
)

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
        display_name, avatar_url, remaining_changes = vlog_comment_service.get_profile(ip_address)
        return json_response({
            "comments": comments,
            "total": total,
            "page": page,
            "limit": limit,
            "display_name": display_name,
            "avatar_url": avatar_url,
            "remaining_changes": remaining_changes,
        })

    vlog_id = data["vlog_id"]
    text = data["text"]
    ip_address = data["ip_address"]
    comment_id = vlog_comment_service.add_comment(vlog_id, ip_address, text)
    return status_response("success", comment_id=comment_id)

def vlog_like_comment_route():
    form = VlogCommentRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    comment_id = data["comment_id"]
    ip_address = data["ip_address"]
    result = vlog_comment_service.toggle_like(comment_id, ip_address)
    if result is None:
        return status_response("error", COMMENT_NOT_FOUND_ERROR, status.NOT_FOUND)

    return status_response("success", **result)

def vlog_delete_comment_route(comment_id=None):
    form = VlogCommentRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    result = vlog_comment_service.delete_comment(data.get("comment_id") or comment_id, data["ip_address"])
    if result is None:
        return status_response("error", COMMENT_NOT_FOUND_ERROR, status.NOT_FOUND)
    if result is False:
        return status_response("error", COMMENT_DELETE_FORBIDDEN, status.FORBIDDEN)

    return status_response("success", COMMENT_DELETE_SUCCESS)

def vlog_delete_all_comments_route():
    form = VlogCommentRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    deleted = vlog_comment_service.delete_all_comments(data["vlog_id"], data["ip_address"])
    return status_response("success", COMMENT_DELETE_ALL_SUCCESS, deleted=deleted)
