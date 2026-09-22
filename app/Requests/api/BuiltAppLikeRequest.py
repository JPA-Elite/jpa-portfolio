from flask import request, jsonify
from app.Requests.api.BaseRequest import BaseRequest


class BuiltAppLikeRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "counts" in route:
            return self._validate_counts()
        if "toggle" in route or "vote" in route:
            return self._validate_toggle()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_counts(self):
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        app_id = str(self._get_args("app_id", "")).strip()
        return self._success_response({"app_id": app_id, "client_ip": client_ip})

    def _validate_toggle(self):
        data = request.get_json(silent=True) or {}
        app_id = data.get("app_id")
        is_like = data.get("is_like", True)
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        if not self._require("app_id", app_id):
            return None, self._error_response(400)

        return self._success_response({
            "app_id": app_id,
            "is_like": self._parse_bool(is_like, True),
            "client_ip": client_ip,
        })
