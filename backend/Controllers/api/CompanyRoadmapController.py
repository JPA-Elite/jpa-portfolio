import json

from flask import jsonify, request

from backend.Repositories.CompanyRoadmapRepository import CompanyRoadmapRepository
from backend.Services.CompanyRoadmapService import CompanyRoadmapService
from backend.configurations import SortOrder, SortOrderStr
from backend.extensions import cache
from backend.utils import clear_cache_by_prefix, get_cache_data

company_roadmap_service = CompanyRoadmapService(repository=CompanyRoadmapRepository())

def _get_i18n_text_map(field_name: str):
    return {
        "en": request.form.get(field_name, "").strip(),
        "ceb": request.form.get(f"{field_name}_ceb", "").strip(),
        "fil_PH": request.form.get(f"{field_name}_fil", "").strip(),
    }

def _get_i18n_highlights_map():
    return {
        "en": request.form.get("highlights", ""),
        "ceb": request.form.get("highlights_ceb", ""),
        "fil_PH": request.form.get("highlights_fil", ""),
    }

def company_roadmap_list_route():
    cached_data, cache_key = get_cache_data("admin.api.company_roadmap_list", request.args)
    if cached_data:
        return jsonify(cached_data)

    try:
        company_roadmap_service.seed_default_company_roadmaps_if_empty()
    except Exception:
        pass

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search_query = (request.args.get("search") or "").strip()
    employment_type_filter = (request.args.get("employment_type") or "").strip()

    is_active_raw = (request.args.get("is_active") or "").strip().lower()
    is_active_filter = None
    if is_active_raw in {"1", "true", "yes", "on"}:
        is_active_filter = True
    elif is_active_raw in {"0", "false", "no", "off"}:
        is_active_filter = False

    order = (
        SortOrder.DESC
        if request.args.get("order", "desc").upper() == SortOrderStr.DESC
        else SortOrder.ASC
    )

    roadmaps, total = company_roadmap_service.get_paginated_company_roadmaps(
        page,
        per_page,
        order,
        search_query,
        employment_type_filter=employment_type_filter,
        is_active_filter=is_active_filter,
    )
    response_data = {
        "roadmaps": [roadmap.to_dict() for roadmap in roadmaps],
        "total_roadmaps": total,
        "total_pages": (total + per_page - 1) // per_page,
        "search": search_query,
        "employment_type": employment_type_filter,
        "is_active": is_active_filter,
    }
    cache.set(cache_key, response_data, timeout=300)
    return jsonify(response_data)

def add_company_roadmap_route():
    activities_meta = request.form.get("activities_meta")

    data = {
        "company_name": request.form.get("company_name", "").strip(),
        "role_title": request.form.get("role_title", "").strip(),
        "period": request.form.get("period", "").strip(),
        "employment_type": request.form.get("employment_type", "experience").strip(),
        "location": request.form.get("location", "").strip(),
        "definition": request.form.get("definition", "").strip(),
        "definition_i18n": _get_i18n_text_map("definition"),
        "summary": request.form.get("summary", "").strip(),
        "summary_i18n": _get_i18n_text_map("summary"),
        "role_title_i18n": _get_i18n_text_map("role_title"),
        "highlights": request.form.get("highlights", ""),
        "highlights_i18n": _get_i18n_highlights_map(),
        "accent_color": request.form.get("accent_color", "#2962ff"),
        "sort_order": int(request.form.get("sort_order", 0) or 0),
        "is_active": request.form.get("is_active", "true").lower() in ("1", "true", "yes", "on"),
        "cover_image_file": request.files.get("cover_image_file"),
        "activity_files": request.files,
        "activities_meta": json.loads(activities_meta) if activities_meta else [],
    }

    roadmap_id = company_roadmap_service.add_company_roadmap(data)
    _clear_company_roadmap_caches()
    return jsonify({"message": "Company roadmap entry added successfully.", "roadmap_id": roadmap_id}), 201

def update_company_roadmap_route(roadmap_id):
    activities_meta = request.form.get("activities_meta")
    is_active_raw = request.form.get("is_active")
    sort_order = request.form.get("sort_order")

    data = {
        "company_name": request.form.get("company_name"),
        "role_title": request.form.get("role_title"),
        "period": request.form.get("period"),
        "employment_type": request.form.get("employment_type"),
        "location": request.form.get("location"),
        "definition": request.form.get("definition"),
        "definition_i18n": _get_i18n_text_map("definition"),
        "summary": request.form.get("summary"),
        "summary_i18n": _get_i18n_text_map("summary"),
        "role_title_i18n": _get_i18n_text_map("role_title"),
        "highlights": request.form.get("highlights"),
        "highlights_i18n": _get_i18n_highlights_map(),
        "accent_color": request.form.get("accent_color"),
        "sort_order": int(sort_order) if sort_order not in (None, "") else None,
        "is_active": (
            is_active_raw.lower() in ("1", "true", "yes", "on")
            if is_active_raw is not None
            else None
        ),
        "cover_image_file": request.files.get("cover_image_file"),
        "activity_files": request.files,
        "activities_meta": json.loads(activities_meta) if activities_meta else None,
    }

    success = company_roadmap_service.update_company_roadmap(roadmap_id, data)
    if not success:
        return jsonify({"message": "Company roadmap entry not found."}), 404

    _clear_company_roadmap_caches()
    return jsonify({"message": "Company roadmap entry updated successfully."}), 200

def delete_company_roadmap_route(roadmap_id):
    success = company_roadmap_service.delete_company_roadmap(roadmap_id)
    if not success:
        return jsonify({"message": "Company roadmap entry not found."}), 404

    _clear_company_roadmap_caches()
    return jsonify({"message": "Company roadmap entry deleted successfully."}), 200

def _clear_company_roadmap_caches():
    clear_cache_by_prefix("admin.api.company_roadmap_list:")
    clear_cache_by_prefix("profile_ui_")

