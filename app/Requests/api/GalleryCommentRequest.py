from flask import request, jsonify
from app.Requests.api.BaseRequest import BaseRequest


class GalleryCommentRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "like" in route:
            return self._validate_toggle_like()
        if "delete" in route:
            return self._validate_delete()
        if "comments" in route:
            if request.method == "GET":
                return self._validate_list()
            return self._validate_store()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_list(self):
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

        if request.method == "GET":
            gallery_id = self._get_args("gallery_id")
            page = self._get_int("page", 1)
            limit = self._get_int("limit", 10)
            return self._success_response({
                "gallery_id": gallery_id,
                "page": page,
                "limit": limit,
                "ip_address": ip_address,
            })

        data = request.get_json(silent=True) or {}
        gallery_id = data.get("gallery_id")
        text = data.get("text")

        return self._success_response({
            "gallery_id": gallery_id,
            "text": text,
            "ip_address": ip_address,
        })

    def _validate_store(self):
        data = request.get_json(silent=True) or {}
        gallery_id = data.get("gallery_id")
        text = data.get("text")
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

        return self._success_response({
            "gallery_id": gallery_id,
            "text": text,
            "ip_address": ip_address,
        })

    def _validate_delete(self):
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
        comment_id = (request.view_args or {}).get("comment_id")

        if comment_id:
            return self._success_response({
                "comment_id": comment_id,
                "ip_address": ip_address,
            })

        data = request.get_json(silent=True) or {}
        gallery_id = data.get("gallery_id")

        if not self._require("gallery_id", gallery_id):
            return None, self._error_response(400)

        return self._success_response({
            "gallery_id": gallery_id,
            "ip_address": ip_address,
        })

    def _validate_toggle_like(self):
        data = request.get_json(silent=True) or {}
        comment_id = data.get("comment_id")
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

        if not self._require("comment_id", comment_id):
            return None, self._error_response(400)

        return self._success_response({
            "comment_id": comment_id,
            "ip_address": ip_address,
        })
