import os
import tempfile

from flask import jsonify, request

from app.Repositories.UserDisplayNameRepository import UserDisplayNameRepository
from app.Requests.api.CommentAvatarRequest import CommentAvatarRequest
from app.Requests.api.CommentAvatarUploadRequest import CommentAvatarUploadRequest
from app.Services.UserDisplayNameService import UserDisplayNameService
from app.configurations import HTTPMethod as http
from app.constants.cloudinary import CloudinaryFolders, CloudinaryResourceType
from app.constants.messages import (
    AVATAR_CHANGE_LIMIT_ERROR,
    COMMENT_AVATAR_SIZE_ERROR,
    COMMENT_AVATAR_UPLOAD_ERROR,
    COMMENT_AVATAR_UPLOAD_SUCCESS,
)
from app.utils import cleanup_uploaded_files, compress_avatar_image, upload_file_to_cloudinary

MAX_COMPRESSED_AVATAR_BYTES = 2 * 1024 * 1024

user_display_name_service = UserDisplayNameService(repository=UserDisplayNameRepository())


def comment_avatar_route():
    form = CommentAvatarRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    if request.method == http.GET:
        avatar_url, remaining = user_display_name_service.get_avatar_status(data["ip_address"])
        return jsonify({"avatar_url": avatar_url, "remaining_avatar_changes": remaining})

    if request.method == http.DELETE:
        current_url, remaining = user_display_name_service.get_avatar_status(data["ip_address"])
        if not current_url:
            return jsonify({"status": "success", "avatar_url": None})
        if remaining <= 0:
            return jsonify({
                "errors": {"avatar": AVATAR_CHANGE_LIMIT_ERROR},
                "code": "avatar_limit_reached",
                "remaining_avatar_changes": 0,
            }), 429
        saved_url, previous_url = user_display_name_service.save_avatar(data["ip_address"], None)
        if previous_url and str(previous_url).startswith("http"):
            cleanup_uploaded_files(image_url=previous_url)
        return jsonify({"status": "success", "avatar_url": None})

    avatar_url = data["avatar_url"]
    saved_url, previous_url = user_display_name_service.save_avatar(data["ip_address"], avatar_url)
    if saved_url is None:
        return jsonify({
            "errors": {"avatar_url": AVATAR_CHANGE_LIMIT_ERROR},
            "code": "avatar_limit_reached",
            "remaining_avatar_changes": 0,
        }), 429
    if previous_url and str(previous_url).startswith("http"):
        cleanup_uploaded_files(image_url=previous_url)
    return jsonify({"status": "success", "avatar_url": avatar_url})


def comment_avatar_upload_route():
    form = CommentAvatarUploadRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    new_avatar_url = None
    try:
        fd, path = tempfile.mkstemp()
        os.close(fd)
        data["avatar_file"].save(path)

        webp_path = compress_avatar_image(path)

        if os.path.getsize(webp_path) > MAX_COMPRESSED_AVATAR_BYTES:
            os.remove(path)
            os.remove(webp_path)
            return jsonify({
                "errors": {"avatar": COMMENT_AVATAR_SIZE_ERROR},
                "code": "avatar_too_large",
            }), 400

        new_avatar_url = upload_file_to_cloudinary(
            webp_path,
            resource_type=CloudinaryResourceType.IMAGE,
            folder=CloudinaryFolders.AVATAR,
        )

        os.remove(path)
        if webp_path != path:
            os.remove(webp_path)

        if not new_avatar_url or str(new_avatar_url).startswith("Error"):
            cleanup_uploaded_files(image_url=new_avatar_url)
            return jsonify({"errors": {"_global": COMMENT_AVATAR_UPLOAD_ERROR}}), 500

        saved_url, previous_url = user_display_name_service.save_avatar(data["ip_address"], new_avatar_url)
        if saved_url is None:
            cleanup_uploaded_files(image_url=new_avatar_url)
            return jsonify({
                "errors": {"avatar": AVATAR_CHANGE_LIMIT_ERROR},
                "code": "avatar_limit_reached",
                "remaining_avatar_changes": 0,
            }), 429
        if previous_url and str(previous_url).startswith("http"):
            cleanup_uploaded_files(image_url=previous_url)

        return jsonify({
            "status": "success",
            "avatar_url": new_avatar_url,
            "message": COMMENT_AVATAR_UPLOAD_SUCCESS,
        })
    except Exception as error:
        cleanup_uploaded_files(image_url=new_avatar_url)
        return jsonify({"errors": {"_global": f"{COMMENT_AVATAR_UPLOAD_ERROR}: {error}"}}), 500
