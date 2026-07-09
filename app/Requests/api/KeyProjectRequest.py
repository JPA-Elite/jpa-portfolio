import json
from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest
from app.configurations import SortOrder, SortOrderStr


class KeyProjectRequest(BaseRequest):
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
        status_filter = str(self._get_args("status", "")).strip().lower()
        if status_filter not in {"", "shipped", "building", "planned"}:
            status_filter = ""

        is_active_raw = str(self._get_args("is_active", "")).strip().lower()
        is_active_filter = None
        if is_active_raw in {"1", "true", "yes", "on"}:
            is_active_filter = True
        elif is_active_raw in {"0", "false", "no", "off"}:
            is_active_filter = False

        order = (
            SortOrder.DESC
            if str(self._get_args("order", "desc")).upper() == SortOrderStr.DESC
            else SortOrder.ASC
        )

        return self._success_response({
            "page": page,
            "per_page": per_page,
            "search_query": search_query,
            "status_filter": status_filter,
            "is_active_filter": is_active_filter,
            "order": order,
        })

    def _validate_store(self):
        title = self._get_form("title")
        description = self._get_form("description")
        image_file = self._get_file("image_file")
        slides_meta = self._get_form("slides_meta")
        sort_order = self._get_form("sort_order", 0)

        data = {
            "title": self._parse_json_field(title),
            "description": self._parse_json_field(description),
            "image_file": image_file,
            "slide_files": request.files,
            "slides_meta": json.loads(slides_meta) if slides_meta else [],
            "stack": str(self._get_form("stack", "")).strip(),
            "status": str(self._get_form("status", "planned")).strip(),
            "demo_url": str(self._get_form("demo_url", "")).strip(),
            "repo_url": str(self._get_form("repo_url", "")).strip(),
            "sort_order": int(sort_order or 0),
            "is_active": self._parse_bool(self._get_form("is_active", "true")),
        }

        return self._success_response(data)

    def _validate_update(self):
        title = self._get_form("title")
        description = self._get_form("description")
        image_file = self._get_file("image_file")
        slides_meta = self._get_form("slides_meta")
        sort_order = self._get_form("sort_order")
        is_active_raw = self._get_form("is_active")

        data = {
            "title": self._parse_json_field(title),
            "description": self._parse_json_field(description),
            "image_file": image_file,
            "slide_files": request.files,
            "slides_meta": json.loads(slides_meta) if slides_meta else None,
            "stack": self._get_form("stack"),
            "status": self._get_form("status"),
            "demo_url": self._get_form("demo_url"),
            "repo_url": self._get_form("repo_url"),
            "sort_order": int(sort_order) if sort_order not in (None, "") else None,
            "is_active": (
                self._parse_bool(is_active_raw)
                if is_active_raw is not None
                else None
            ),
        }

        return self._success_response(data)

    def _validate_delete(self):
        return self._success_response({})
