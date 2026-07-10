from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest
from app.configurations import SortOrder, SortOrderStr


class MusicRequest(BaseRequest):
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
        category = str(self._get_args("category", "")).strip()

        return self._success_response({
            "page": page,
            "per_page": per_page,
            "search_query": search_query,
            "order": order,
            "category": category,
        })

    def _validate_store(self):
        data = {
            "title": str(self._get_form("title", "")).strip(),
            "artist": str(self._get_form("artist", "")).strip(),
            "lyrics": str(self._get_form("lyrics", "")).strip(),
            "category": str(self._get_form("category", "All")).strip(),
            "music_file": self._get_file("music_file"),
            "image_file": self._get_file("image_file"),
            "music_url_input": str(self._get_form("music_url_input", "")).strip(),
            "music_source_type": str(self._get_form("music_source_type", "file")).strip(),
        }

        return self._success_response(data)

    def _validate_update(self):
        data = {
            "title": self._get_form("title"),
            "artist": self._get_form("artist"),
            "lyrics": self._get_form("lyrics"),
            "category": self._get_form("category"),
            "music_file": self._get_file("music_file"),
            "image_file": self._get_file("image_file"),
            "music_url_input": self._get_form("music_url_input"),
            "music_source_type": self._get_form("music_source_type", "file"),
        }

        return self._success_response(data)

    def _validate_delete(self):
        return self._success_response({})
