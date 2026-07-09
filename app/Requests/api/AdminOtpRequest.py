from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest


class AdminOtpRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "send" in route:
            return self._validate_send()
        if "verify" in route:
            return self._validate_verify()
        if "reset" in route:
            return self._validate_reset()
        if "email" in route and "get" in route:
            return self._validate_email_get()
        if "email" in route and "save" in route:
            return self._validate_email_save()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_send(self):
        payload = request.get_json(silent=True) or {}
        email = str(payload.get("email", "")).strip()
        return self._success_response({"email": email})

    def _validate_verify(self):
        payload = request.get_json(silent=True) or {}
        otp = str(payload.get("otp", "")).strip()

        if not self._require("otp", otp):
            return None, self._error_response(400)

        return self._success_response({"otp": otp})

    def _validate_reset(self):
        return self._success_response({})

    def _validate_email_get(self):
        return self._success_response({})

    def _validate_email_save(self):
        payload = request.get_json(silent=True) or {}
        email = str(payload.get("email", "")).strip()

        if not self._require("email", email, message="Missing email."):
            return None, self._error_response(400)

        return self._success_response({"email": email})
