from flask import request
from app.Requests.api.BaseRequest import BaseRequest


class AuthRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "update" in route and "profile" in route:
            return self._validate_update_profile()

        return self._unknown_route()

    def _validate_update_profile(self):
        return self._success_response({})
