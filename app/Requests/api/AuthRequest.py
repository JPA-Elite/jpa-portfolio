from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest


class AuthRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "update" in route and "profile" in route:
            return self._validate_update_profile()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_update_profile(self):
        return self._success_response({})
