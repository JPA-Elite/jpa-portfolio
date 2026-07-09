from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest


class PageRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "gallery" in route and "page" in route:
            return self._validate_gallery()
        if "vlog" in route:
            return self._validate_vlog()
        if "profile" in route:
            return self._validate_profile()
        if "add_portfolio" in route:
            return self._validate_add_portfolio()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_gallery(self):
        search_query = str(self._get_args("search", "")).strip()
        tags_query = str(self._get_args("tags", "")).strip()
        page = self._get_int("page", 1)
        return self._success_response({
            "search_query": search_query,
            "tags_query": tags_query,
            "page": page,
        })

    def _validate_vlog(self):
        search_query = str(self._get_args("search", "")).strip()
        tags_query = str(self._get_args("tags", "")).strip()
        page = self._get_int("page", 1)
        return self._success_response({
            "search_query": search_query,
            "tags_query": tags_query,
            "page": page,
        })

    def _validate_profile(self):
        return self._success_response({})

    def _validate_add_portfolio(self):
        return self._success_response({})
