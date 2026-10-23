from flask import request

from app.Requests.api.BaseRequest import BaseRequest
from app.configurations import HTTPMethod as http
from app.constants.avatars import PRESET_AVATARS


class CommentAvatarRequest(BaseRequest):
    def validated(self):
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

        if request.method in (http.GET, http.DELETE):
            return self._success_response({"ip_address": ip_address})

        if request.method != http.POST:
            return self._success_response({"ip_address": ip_address})

        data = request.get_json(silent=True) or {}
        avatar_url = (data.get("avatar_url") or "").strip()

        if not self._require("avatar_url", avatar_url):
            return None, *self._error_response(400)

        if avatar_url not in PRESET_AVATARS:
            self._errors["avatar_url"] = "Invalid avatar selection."
            return None, *self._error_response(400)

        return self._success_response({
            "ip_address": ip_address,
            "avatar_url": avatar_url,
        })
