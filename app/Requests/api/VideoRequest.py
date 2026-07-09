from flask import jsonify, request
import json
from app.Requests.api.BaseRequest import BaseRequest
from app.configurations import SortOrder, SortOrderStr


class VideoRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "list" in route:
            return self._validate_list()
        if "add" in route:
            return self._validate_store()
        if "update" in route:
            return self._validate_update()
        if "delete" in route:
            return self._validate_delete()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_list(self):
        page = self._get_int("page", 1)
        per_page = self._get_int("per_page", 10)
        search_query = str(self._get_args("search", "")).strip()
        order = (
            SortOrder.DESC
            if str(self._get_args("order", "desc")).upper() == SortOrderStr.DESC
            else SortOrder.ASC
        )

        return self._success_response({
            "page": page,
            "per_page": per_page,
            "search_query": search_query,
            "order": order,
        })

    def _validate_store(self):
        title = self._get_form("title")
        description = self._get_form("description")
        video_file = self._get_file("video_file")
        tags = self._get_form("tags")

        data = {
            "title": self._parse_json_field(title),
            "description": self._parse_json_field(description),
            "video_file": video_file,
            "tags": self._parse_json_field(tags) if tags else [],
        }

        return self._success_response(data)

    def _validate_update(self):
        title = self._get_form("title")
        description = self._get_form("description")
        video_file = self._get_file("video_file")
        tags = self._get_form("tags")

        data = {
            "title": self._parse_json_field(title),
            "description": self._parse_json_field(description),
            "video_file": video_file,
            "tags": self._parse_json_field(tags) if tags else [],
        }

        return self._success_response(data)

    def _validate_delete(self):
        return self._success_response({})
