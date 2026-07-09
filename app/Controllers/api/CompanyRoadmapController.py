import json
from flask import jsonify, request
from app.Repositories.CompanyRoadmapRepository import CompanyRoadmapRepository
from app.Services.CompanyRoadmapService import CompanyRoadmapService
from app.configurations import SortOrder, SortOrderStr
from app.extensions import cache
from app.Requests.api.CompanyRoadmapRequest import CompanyRoadmapRequest
from app.utils import clear_cache_by_prefix, get_cache_data

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

    form = CompanyRoadmapRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    roadmaps, total = company_roadmap_service.get_paginated_company_roadmaps(
        data["page"],
        data["per_page"],
        data["order"],
        data["search_query"],
        employment_type_filter=data["employment_type_filter"],
        is_active_filter=data["is_active_filter"],
    )
    response_data = {
        "roadmaps": [roadmap.to_dict() for roadmap in roadmaps],
        "total_roadmaps": total,
        "total_pages": (total + data["per_page"] - 1) // data["per_page"],
        "search": data["search_query"],
        "employment_type": data["employment_type_filter"],
        "is_active": data["is_active_filter"],
    }
    cache.set(cache_key, response_data, timeout=300)
    return jsonify(response_data)


def add_company_roadmap_route():
    form = CompanyRoadmapRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    roadmap_id = company_roadmap_service.add_company_roadmap(data)
    _clear_company_roadmap_caches()
    return jsonify({"message": "Company roadmap entry added successfully.", "roadmap_id": roadmap_id}), 201


def update_company_roadmap_route(roadmap_id):
    form = CompanyRoadmapRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = company_roadmap_service.update_company_roadmap(roadmap_id, data)
    if not success:
        return jsonify({"message": "Company roadmap entry not found."}), 404

    _clear_company_roadmap_caches()
    return jsonify({"message": "Company roadmap entry updated successfully."}), 200


def delete_company_roadmap_route(roadmap_id):
    form = CompanyRoadmapRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = company_roadmap_service.delete_company_roadmap(roadmap_id)
    if not success:
        return jsonify({"message": "Company roadmap entry not found."}), 404

    _clear_company_roadmap_caches()
    return jsonify({"message": "Company roadmap entry deleted successfully."}), 200


def _clear_company_roadmap_caches():
    clear_cache_by_prefix("admin.api.company_roadmap_list:")
    clear_cache_by_prefix("profile_ui_")

