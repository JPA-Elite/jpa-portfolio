import json
from app.Repositories.KeyProjectRepository import KeyProjectRepository
from app.Services.KeyProjectService import KeyProjectService
from app.core.configurations import SortOrder, SortOrderStr, HTTPStatus as status
from app.core.responses import created_response, json_response, message_response
from app.Requests.api.KeyProjectRequest import KeyProjectRequest
from app.utils.cache import clear_cache_by_prefix

key_project_service = KeyProjectService(repository=KeyProjectRepository())


def key_project_list_route():
    try:
        key_project_service.seed_default_projects_if_empty()
    except Exception:
        pass

    form = KeyProjectRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    project_list, total = key_project_service.get_paginated_key_projects(
        data["page"],
        data["per_page"],
        data["order"],
        data["search_query"],
        status_filter=data["status_filter"],
        is_active_filter=data["is_active_filter"],
    )
    response_data = {
        "projects": [project.to_dict() for project in project_list],
        "total_projects": total,
        "total_pages": (total + data["per_page"] - 1) // data["per_page"],
        "search": data["search_query"],
        "status": data["status_filter"],
        "is_active": data["is_active_filter"],
    }
    return json_response(response_data)

def add_key_project_route():
    form = KeyProjectRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    project_id = key_project_service.add_key_project(data)
    _clear_key_project_caches()
    return created_response("Key project added successfully.", project_id=project_id)

def update_key_project_route(project_id):
    form = KeyProjectRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = key_project_service.update_key_project(project_id, data)
    if not success:
        return message_response("Key project not found.", status.NOT_FOUND)

    _clear_key_project_caches()
    return message_response("Key project updated successfully.")

def delete_key_project_route(project_id):
    form = KeyProjectRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = key_project_service.delete_key_project(project_id)
    if not success:
        return message_response("Key project not found.", status.NOT_FOUND)

    _clear_key_project_caches()
    return message_response("Key project deleted successfully.")

def _clear_key_project_caches():
    clear_cache_by_prefix("profile_ui_")
