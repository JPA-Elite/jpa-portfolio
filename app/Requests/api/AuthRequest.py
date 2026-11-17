from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest
from app.configurations import HTTPStatus as status


class AuthRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "update" in route and "profile" in route:
            return self._validate_update_profile()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), status.BAD_REQUEST

    def _validate_update_profile(self):
        return self._success_response({})
