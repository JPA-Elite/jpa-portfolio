import json
from flask import jsonify, request
from app.Requests.api.BaseRequest import BaseRequest
from app.configurations import SortOrder, SortOrderStr


class CompanyRoadmapRequest(BaseRequest):
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
        employment_type_filter = str(self._get_args("employment_type", "")).strip()

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
            "employment_type_filter": employment_type_filter,
            "is_active_filter": is_active_filter,
            "order": order,
        })

    def _validate_store(self):
        activities_meta = self._get_form("activities_meta")

        data = {
            "company_name": str(self._get_form("company_name", "")).strip(),
            "role_title": str(self._get_form("role_title", "")).strip(),
            "period": str(self._get_form("period", "")).strip(),
            "employment_type": str(self._get_form("employment_type", "experience")).strip(),
            "location": str(self._get_form("location", "")).strip(),
            "definition": str(self._get_form("definition", "")).strip(),
            "definition_i18n": {
                "en": str(self._get_form("definition", "")).strip(),
                "ceb": str(self._get_form("definition_ceb", "")).strip(),
                "fil_PH": str(self._get_form("definition_fil", "")).strip(),
            },
            "summary": str(self._get_form("summary", "")).strip(),
            "summary_i18n": {
                "en": str(self._get_form("summary", "")).strip(),
                "ceb": str(self._get_form("summary_ceb", "")).strip(),
                "fil_PH": str(self._get_form("summary_fil", "")).strip(),
            },
            "role_title_i18n": {
                "en": str(self._get_form("role_title", "")).strip(),
                "ceb": str(self._get_form("role_title_ceb", "")).strip(),
                "fil_PH": str(self._get_form("role_title_fil", "")).strip(),
            },
            "highlights": self._get_form("highlights"),
            "highlights_i18n": {
                "en": self._get_form("highlights"),
                "ceb": self._get_form("highlights_ceb"),
                "fil_PH": self._get_form("highlights_fil"),
            },
            "accent_color": str(self._get_form("accent_color", "#2962ff")).strip(),
            "sort_order": self._get_form_int("sort_order", 0),
            "is_active": self._parse_bool(self._get_form("is_active", "true")),
            "cover_image_file": self._get_file("cover_image_file"),
            "activity_files": request.files,
            "activities_meta": json.loads(activities_meta) if activities_meta else [],
        }

        return self._success_response(data)

    def _validate_update(self):
        activities_meta = self._get_form("activities_meta")
        is_active_raw = self._get_form("is_active")
        sort_order = self._get_form("sort_order")

        data = {
            "company_name": self._get_form("company_name"),
            "role_title": self._get_form("role_title"),
            "period": self._get_form("period"),
            "employment_type": self._get_form("employment_type"),
            "location": self._get_form("location"),
            "definition": self._get_form("definition"),
            "definition_i18n": {
                "en": str(self._get_form("definition", "")).strip(),
                "ceb": str(self._get_form("definition_ceb", "")).strip(),
                "fil_PH": str(self._get_form("definition_fil", "")).strip(),
            },
            "summary": self._get_form("summary"),
            "summary_i18n": {
                "en": str(self._get_form("summary", "")).strip(),
                "ceb": str(self._get_form("summary_ceb", "")).strip(),
                "fil_PH": str(self._get_form("summary_fil", "")).strip(),
            },
            "role_title_i18n": {
                "en": str(self._get_form("role_title", "")).strip(),
                "ceb": str(self._get_form("role_title_ceb", "")).strip(),
                "fil_PH": str(self._get_form("role_title_fil", "")).strip(),
            },
            "highlights": self._get_form("highlights"),
            "highlights_i18n": {
                "en": self._get_form("highlights"),
                "ceb": self._get_form("highlights_ceb"),
                "fil_PH": self._get_form("highlights_fil"),
            },
            "accent_color": self._get_form("accent_color"),
            "sort_order": int(sort_order) if sort_order not in (None, "") else None,
            "is_active": (
                self._parse_bool(is_active_raw)
                if is_active_raw is not None
                else None
            ),
            "cover_image_file": self._get_file("cover_image_file"),
            "activity_files": request.files,
            "activities_meta": json.loads(activities_meta) if activities_meta else None,
        }

        return self._success_response(data)

    def _validate_delete(self):
        return self._success_response({})
