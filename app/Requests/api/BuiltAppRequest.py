import json
from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest
from app.configurations import SortOrder, SortOrderStr


class BuiltAppRequest(BaseRequest):
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
        platform_filter = str(self._get_args("platform", "")).strip().lower()
        if platform_filter not in {"", "mobile", "desktop"}:
            platform_filter = ""

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
            "platform_filter": platform_filter,
            "is_active_filter": is_active_filter,
            "order": order,
        })

    def _validate_store(self):
        name = self._parse_json_field(self._get_form("name"))
        short_description = self._parse_json_field(self._get_form("short_description"))
        full_description = self._parse_json_field(self._get_form("full_description"))
        snapshots_meta = self._get_form("snapshots_meta")
        sort_order = self._get_form("sort_order", 0)

        data = {
            "name": name,
            "short_description": short_description,
            "full_description": full_description,
            "slug": str(self._get_form("slug", "")).strip(),
            "platform": str(self._get_form("platform", "Mobile")).strip(),
            "version": str(self._get_form("version", "")).strip(),
            "icon": str(self._get_form("icon", "apps-outline")).strip(),
            "download_url": str(self._get_form("download_url", "")).strip(),
            "snapshot_files": request.files,
            "snapshots_meta": json.loads(snapshots_meta) if snapshots_meta else None,
            "sort_order": int(sort_order or 0),
            "is_active": self._parse_bool(self._get_form("is_active", "true")),
        }

        if not isinstance(data["name"], dict) or not (data["name"].get("en") or "").strip():
            return None, jsonify({"errors": {"name.en": "English name is required."}}), 400

        return self._success_response(data)

    def _validate_update(self):
        name = self._parse_json_field(self._get_form("name"))
        short_description = self._parse_json_field(self._get_form("short_description"))
        full_description = self._parse_json_field(self._get_form("full_description"))
        snapshots_meta = self._get_form("snapshots_meta")
        sort_order = self._get_form("sort_order")
        is_active_raw = self._get_form("is_active")

        data = {
            "name": name if isinstance(name, dict) and any(str(v or "").strip() for v in name.values()) else None,
            "short_description": short_description if isinstance(short_description, dict) else None,
            "full_description": full_description if isinstance(full_description, dict) else None,
            "slug": self._get_form("slug"),
            "platform": self._get_form("platform"),
            "version": self._get_form("version"),
            "icon": self._get_form("icon"),
            "download_url": self._get_form("download_url"),
            "snapshot_files": request.files,
            "snapshots_meta": json.loads(snapshots_meta) if snapshots_meta else None,
            "sort_order": int(sort_order) if sort_order not in (None, "") else None,
            "is_active": (
                self._parse_bool(is_active_raw)
                if is_active_raw is not None
                else None
            ),
        }

        data["slug"] = str(data["slug"]).strip() if data["slug"] is not None else None
        for key in ("platform", "version", "icon", "download_url"):
            data[key] = str(data[key]).strip() if data[key] is not None else None

        return self._success_response(data)

    def _validate_delete(self):
        return self._success_response({})
