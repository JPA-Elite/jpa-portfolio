from flask import request

from app.Requests.api.BaseRequest import BaseRequest
from app.Services.UserDisplayNameService import UserDisplayNameService
from app.configurations import HTTPMethod as http


class UserDisplayNameRequest(BaseRequest):
    def validated(self):
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

        if request.method == http.GET:
            return self._success_response({"ip_address": ip_address})

        data = request.get_json(silent=True) or {}
        display_name = (data.get("display_name") or "").strip()

        if not self._require("display_name", display_name):
            return None, self._error_response(400)

        if len(display_name) > UserDisplayNameService.MAX_NAME_LENGTH:
            self._errors["display_name"] = (
                f"Display name must be {UserDisplayNameService.MAX_NAME_LENGTH} characters or fewer."
            )
            return None, self._error_response(400)

        return self._success_response({
            "ip_address": ip_address,
            "display_name": display_name,
        })
