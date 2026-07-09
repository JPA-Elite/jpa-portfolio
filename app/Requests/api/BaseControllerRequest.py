from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest


class BaseControllerRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "change_language" in route:
            return self._validate_change_language()
        if "delete_page_system_info" in route:
            return self._validate_delete_page_system_info()
        if "download_song" in route:
            return self._validate_download_song()
        if "client_ip" in route:
            return self._validate_client_ip()
        if "proxy_audio" in route:
            return self._validate_proxy_audio()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_change_language(self):
        return self._success_response({})

    def _validate_delete_page_system_info(self):
        data = request.get_json(silent=True) or {}
        records = data.get("records", [])
        return self._success_response({"records": records})

    def _validate_download_song(self):
        url = self._get_args("url")
        if not self._require("url", url):
            return None, self._error_response(400)
        return self._success_response({"url": url})

    def _validate_client_ip(self):
        return self._success_response({})

    def _validate_proxy_audio(self):
        url = self._get_args("url")
        if not self._require("url", url):
            return None, self._error_response(400)

        range_header = request.headers.get("Range")
        return self._success_response({"url": url, "range_header": range_header})
