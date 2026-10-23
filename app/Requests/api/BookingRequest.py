import re
from flask import request
from app.Requests.api.BaseRequest import BaseRequest

class BookingRequest(BaseRequest):
    def validated(self):
        payload = request.get_json(silent=True) or {}
        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip()
        preferred_date = str(payload.get("preferred_date", "")).strip()
        preferred_time = str(payload.get("preferred_time", "")).strip()
        message = str(payload.get("message", "")).strip()

        if not self._require("name", name, "Full name is required."):
            return None, *self._error_response(400)
        if len(name) > 50:
            self._errors["name"] = "Full name must be at most 50 characters."
            return None, *self._error_response(400)

        if not self._require("email", email, "Email is required."):
            return None, *self._error_response(400)
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            self._errors["email"] = "Invalid email format."
            return None, *self._error_response(400)

        if not self._require("preferred_date", preferred_date, "Preferred date is required."):
            return None, *self._error_response(400)

        if not self._require("preferred_time", preferred_time, "Preferred time is required."):
            return None, *self._error_response(400)

        if not self._require("message", message, "Message is required."):
            return None, *self._error_response(400)
        if len(message) > 500:
            self._errors["message"] = "Message must be at most 500 characters."
            return None, *self._error_response(400)

        service = str(payload.get("service", "")).strip() or None

        return self._success_response({
            "name": name,
            "email": email,
            "preferred_date": preferred_date,
            "preferred_time": preferred_time,
            "message": message,
            "service": service,
        })
