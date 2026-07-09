from flask import request, jsonify
from app.Requests.api.BaseRequest import BaseRequest


class MusicLikeRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "counts" in route and "batch" in route:
            return self._validate_counts_batch()
        if "counts" in route:
            return self._validate_counts()
        if "toggle" in route:
            return self._validate_toggle()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_counts(self):
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        music_id = str(self._get_args("music_id", "")).strip()
        return self._success_response({"music_id": music_id, "client_ip": client_ip})

    def _validate_counts_batch(self):
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        raw_ids = str(self._get_args("music_ids", "")).strip()
        music_ids = [mid.strip() for mid in raw_ids.split(",") if mid.strip()][:50]
        return self._success_response({"music_ids": music_ids, "client_ip": client_ip})

    def _validate_toggle(self):
        data = request.get_json(silent=True) or {}
        music_id = data.get("music_id")
        is_like = data.get("is_like", True)
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        if not self._require("music_id", music_id):
            return None, self._error_response(400)

        return self._success_response({
            "music_id": music_id,
            "is_like": self._parse_bool(is_like, True),
            "client_ip": client_ip,
        })
