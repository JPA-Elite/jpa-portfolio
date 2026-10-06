from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest
from app.configurations import SortOrder


class DashboardRequest(BaseRequest):
    def validated(self):
        route = request.endpoint or ""

        if "visits" in route and "list" in route:
            return self._validate_visits_list()
        if "visits" in route and "delete" in route:
            return self._validate_visits_delete()
        if "activity" in route and "delete" in route:
            return self._validate_recent_activity_delete()
        if "clear" in route and "visitors" in route:
            return self._validate_clear_all_visitors()
        if "clear" in route and "activity" in route:
            return self._validate_clear_all_activity()
        if "recent" in route:
            return self._validate_recent_activity()
        if "summary" in route:
            return self._validate_summary()

        return None, jsonify({"errors": {"_global": "Unknown route."}}), 400

    def _validate_visits_list(self):
        page = self._get_int("page", 1)
        per_page = self._get_int("perPage", 10)
        try:
            page = max(1, int(page))
        except (TypeError, ValueError):
            page = 1
        try:
            per_page = max(1, min(int(per_page), 100))
        except (TypeError, ValueError):
            per_page = 10
        order_str = str(self._get_args("order", "desc")).lower()
        search = str(self._get_args("search", "")).strip().lower()
        order = SortOrder.DESC if order_str == "desc" else SortOrder.ASC

        return self._success_response({
            "page": page,
            "per_page": per_page,
            "order": order,
            "search": search,
        })

    def _validate_visits_delete(self):
        data = request.get_json(silent=True) or {}
        records = data.get("records", [])
        return self._success_response({"records": records})

    def _validate_recent_activity_delete(self):
        data = request.get_json(silent=True) or {}
        record_ids = data.get("record_ids", [])
        return self._success_response({"record_ids": record_ids})

    def _validate_clear_all_visitors(self):
        return self._success_response({})

    def _validate_clear_all_activity(self):
        return self._success_response({})

    def _validate_recent_activity(self):
        page = self._get_int("page", 1)
        per_page = self._get_int("perPage", 10)
        try:
            page = max(1, int(page))
        except (TypeError, ValueError):
            page = 1
        try:
            per_page = max(1, min(int(per_page), 100))
        except (TypeError, ValueError):
            per_page = 10
        order_str = str(self._get_args("order", "desc")).lower()
        search = str(self._get_args("search", "")).strip()
        order = SortOrder.DESC if order_str == "desc" else SortOrder.ASC

        return self._success_response({
            "page": page,
            "per_page": per_page,
            "order": order,
            "search": search,
        })

    def _validate_summary(self):
        recent_limit = self._get_int("recent_limit", 0)
        try:
            recent_limit = max(0, min(int(recent_limit), 100))
        except (TypeError, ValueError):
            recent_limit = 0
        return self._success_response({"recent_limit": recent_limit})
