from flask import jsonify
from app.Repositories.BuiltAppRepository import BuiltAppRepository
from app.Services.BuiltAppService import BuiltAppService
from app.configurations import SortOrder
from app.Requests.api.BuiltAppRequest import BuiltAppRequest
from app.utils import clear_cache_by_prefix

built_app_service = BuiltAppService(repository=BuiltAppRepository())


def built_app_list_route():
    try:
        built_app_service.seed_default_built_apps_if_empty()
    except Exception:
        pass

    form = BuiltAppRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    app_list, total = built_app_service.get_paginated_built_apps(
        data["page"],
        data["per_page"],
        data["order"],
        data["search_query"],
        platform_filter=data["platform_filter"],
        is_active_filter=data["is_active_filter"],
    )
    response_data = {
        "apps": [app.to_dict() for app in app_list],
        "total_apps": total,
        "total_pages": (total + data["per_page"] - 1) // data["per_page"],
        "search": data["search_query"],
        "platform": data["platform_filter"],
        "is_active": data["is_active_filter"],
    }
    return jsonify(response_data)


def add_built_app_route():
    form = BuiltAppRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    app_id = built_app_service.add_built_app(data)
    _clear_built_app_caches()
    return jsonify({"message": "Built app added successfully.", "app_id": app_id}), 201


def update_built_app_route(app_id):
    form = BuiltAppRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = built_app_service.update_built_app(app_id, data)
    if not success:
        return jsonify({"message": "Built app not found."}), 404

    _clear_built_app_caches()
    return jsonify({"message": "Built app updated successfully."}), 200


def delete_built_app_route(app_id):
    form = BuiltAppRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = built_app_service.delete_built_app(app_id)
    if not success:
        return jsonify({"message": "Built app not found."}), 404

    _clear_built_app_caches()
    return jsonify({"message": "Built app deleted successfully."}), 200


def _clear_built_app_caches():
    clear_cache_by_prefix("portfolio_")
    clear_cache_by_prefix("app_details_")
