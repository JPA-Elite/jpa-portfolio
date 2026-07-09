from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest


class AdminPageRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "admin_login" in route:
            return self._validate_admin_login()
        if "admin_face" in route and request.method == "POST":
            return self._validate_admin_face()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_admin_login(self):
        if request.method == "POST":
            form = request.form
            username = str(form.get("username", "")).strip()
            password = form.get("password", "")
            remember = form.get("remember")

            if not username:
                self._errors["username"] = "Username is required."
            if not password:
                self._errors["password"] = "Password is required."

            if self._errors:
                return None

            return self._success_response({
                "username": username,
                "password": password,
                "remember": remember,
            })

        return self._success_response({})

    def _validate_admin_face(self):
        return self._success_response({})
