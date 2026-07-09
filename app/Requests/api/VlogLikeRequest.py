import json
from flask import request, jsonify
from app.Requests.api.BaseRequest import BaseRequest


class VlogLikeRequest(BaseRequest):
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
        vlog_id = str(self._get_args("vlog_id", "")).strip()
        return self._success_response({"vlog_id": vlog_id, "client_ip": client_ip})

    def _validate_counts_batch(self):
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        raw_vlog_ids = str(self._get_args("vlog_ids", "")).strip()

        vlog_ids = []
        for vlog_id in raw_vlog_ids.split(","):
            normalized = vlog_id.strip()
            if normalized and normalized not in vlog_ids:
                vlog_ids.append(normalized)

        return self._success_response({
            "vlog_ids": vlog_ids[:50],
            "client_ip": client_ip,
        })

    def _validate_toggle(self):
        vlog_id = self._get_form("vlog_id")
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        if not self._require("vlog_id", vlog_id):
            return None, self._error_response(400)

        return self._success_response({
            "vlog_id": json.loads(vlog_id),
            "client_ip": client_ip,
        })
