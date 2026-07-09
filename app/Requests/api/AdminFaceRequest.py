from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest


class AdminFaceRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "register" in route:
            return self._validate_register()
        if "records" in route:
            return self._validate_records()
        if "verify" in route:
            return self._validate_verify()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_register(self):
        payload = request.get_json(silent=True) or {}
        image_b64_list = payload.get("image_b64_list")

        if isinstance(image_b64_list, list) and len(image_b64_list) > 0:
            b64_list = [x for x in image_b64_list if isinstance(x, str)]
        else:
            b64 = payload.get("image_b64")
            if not b64 or not isinstance(b64, str):
                self._errors["image_b64"] = "Missing image_b64"
                return None
            b64_list = [b64]

        if not b64_list:
            self._errors["image_b64"] = "Missing image captures"
            return None

        return self._success_response({"image_b64_list": b64_list})

    def _validate_records(self):
        return self._success_response({})

    def _validate_verify(self):
        payload = request.get_json(silent=True) or {}
        image_b64_list = payload.get("image_b64_list")

        if isinstance(image_b64_list, list) and len(image_b64_list) > 0:
            b64_list = [x for x in image_b64_list if isinstance(x, str)]
        else:
            b64 = payload.get("image_b64")
            if not b64 or not isinstance(b64, str):
                self._errors["image_b64"] = "Missing image_b64"
                return None
            b64_list = [b64]

        if not b64_list:
            self._errors["image_b64"] = "Missing image captures"
            return None

        return self._success_response({"image_b64_list": b64_list})
