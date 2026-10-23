from flask import request, jsonify

from app.Requests.api.BaseRequest import BaseRequest
from app.configurations import HTTPMethod as http

MAX_RAW_AVATAR_BYTES = 20 * 1024 * 1024
ALLOWED_AVATAR_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


class CommentAvatarUploadRequest(BaseRequest):
    def validated(self):
        if request.method != http.POST:
            return None, jsonify({"errors": {"_global": "Method not allowed."}}), 405

        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
        avatar_file = request.files.get("avatar")

        if not avatar_file or not avatar_file.filename:
            self._errors["avatar"] = "Avatar file is required."
            return None, *self._error_response(400)

        extension = avatar_file.filename.rsplit(".", 1)[-1].lower() if "." in avatar_file.filename else ""
        if extension not in ALLOWED_AVATAR_EXTENSIONS:
            self._errors["avatar"] = "Unsupported image type. Use PNG, JPG, WEBP, or GIF."
            return None, *self._error_response(400)

        if len(avatar_file.read()) > MAX_RAW_AVATAR_BYTES:
            self._errors["avatar"] = "Image file is too large to upload. Maximum size is 20MB."
            return None, *self._error_response(400)

        avatar_file.stream.seek(0)

        return self._success_response({
            "ip_address": ip_address,
            "avatar_file": avatar_file,
        })
