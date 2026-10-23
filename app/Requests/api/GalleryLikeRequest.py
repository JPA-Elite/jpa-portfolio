import json
from flask import request, jsonify
from app.Requests.api.BaseRequest import BaseRequest


class GalleryLikeRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "count" in route and "batch" in route:
            return self._validate_counts_batch()
        if "count" in route:
            return self._validate_counts()
        if "add" in route:
            return self._validate_toggle()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_counts(self):
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        gallery_id = str(self._get_args("gallery_id", "")).strip()
        return self._success_response({"gallery_id": gallery_id, "client_ip": client_ip})

    def _validate_counts_batch(self):
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        raw_gallery_ids = str(self._get_args("gallery_ids", "")).strip()

        gallery_ids = []
        for gallery_id in raw_gallery_ids.split(","):
            normalized = gallery_id.strip()
            if normalized and normalized not in gallery_ids:
                gallery_ids.append(normalized)

        return self._success_response({
            "gallery_ids": gallery_ids,
            "client_ip": client_ip,
        })

    def _validate_toggle(self):
        gallery_id = self._get_form("gallery_id")
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        if not self._require("gallery_id", gallery_id):
            return None, *self._error_response(400)

        return self._success_response({
            "gallery_id": json.loads(gallery_id),
            "client_ip": client_ip,
        })
