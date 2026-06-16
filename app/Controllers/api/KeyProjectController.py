import json
from flask import jsonify, request
from app.Repositories.KeyProjectRepository import KeyProjectRepository
from app.Services.KeyProjectService import KeyProjectService
from app.configurations import SortOrder, SortOrderStr
from app.extensions import cache
from app.utils import clear_cache_by_prefix, get_cache_data

key_project_service = KeyProjectService(repository=KeyProjectRepository())

def key_project_list_route():
    cached_data, cache_key = get_cache_data("admin.api.key_project_list", request.args)
    if cached_data:
        return jsonify(cached_data)

    try:
        key_project_service.seed_default_projects_if_empty()
    except Exception:
        pass

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search_query = (request.args.get("search") or "").strip()
    status_filter = (request.args.get("status") or "").strip().lower()
    if status_filter not in {"", "shipped", "building", "planned"}:
        status_filter = ""

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

    project_list, total = key_project_service.get_paginated_key_projects(
        page,
        per_page,
        order,
        search_query,
        status_filter=status_filter,
        is_active_filter=is_active_filter,
    )
    response_data = {
        "projects": [project.to_dict() for project in project_list],
        "total_projects": total,
        "total_pages": (total + per_page - 1) // per_page,
        "search": search_query,
        "status": status_filter,
        "is_active": is_active_filter,
    }
    cache.set(cache_key, response_data, timeout=300)
    return jsonify(response_data)

def add_key_project_route():
    title = request.form.get("title")
    description = request.form.get("description")
    image_file = request.files.get("image_file")
    stack = request.form.get("stack", "")
    status = request.form.get("status", "planned")
    demo_url = request.form.get("demo_url", "")
    repo_url = request.form.get("repo_url", "")
    sort_order = request.form.get("sort_order", 0)
    is_active = request.form.get("is_active", "true").lower() in ("1", "true", "yes", "on")
    slides_meta = request.form.get("slides_meta")

    data = {
        "title": json.loads(title) if title else {},
        "description": json.loads(description) if description else {},
        "image_file": image_file,
        "slide_files": request.files,
        "slides_meta": json.loads(slides_meta) if slides_meta else [],
        "stack": stack,
        "status": status,
        "demo_url": demo_url,
        "repo_url": repo_url,
        "sort_order": int(sort_order or 0),
        "is_active": is_active,
    }

    project_id = key_project_service.add_key_project(data)
    _clear_key_project_caches()
    return jsonify({"message": "Key project added successfully.", "project_id": project_id}), 201

def update_key_project_route(project_id):
    title = request.form.get("title")
    description = request.form.get("description")
    image_file = request.files.get("image_file")
    stack = request.form.get("stack")
    status = request.form.get("status")
    demo_url = request.form.get("demo_url")
    repo_url = request.form.get("repo_url")
    sort_order = request.form.get("sort_order")
    is_active_raw = request.form.get("is_active")
    slides_meta = request.form.get("slides_meta")

    data = {
        "title": json.loads(title) if title else {},
        "description": json.loads(description) if description else {},
        "image_file": image_file,
        "slide_files": request.files,
        "slides_meta": json.loads(slides_meta) if slides_meta else None,
        "stack": stack,
        "status": status,
        "demo_url": demo_url,
        "repo_url": repo_url,
        "sort_order": int(sort_order) if sort_order not in (None, "") else None,
        "is_active": (
            is_active_raw.lower() in ("1", "true", "yes", "on")
            if is_active_raw is not None
            else None
        ),
    }

    success = key_project_service.update_key_project(project_id, data)
    if not success:
        return jsonify({"message": "Key project not found."}), 404

    _clear_key_project_caches()
    return jsonify({"message": "Key project updated successfully."}), 200

def delete_key_project_route(project_id):
    success = key_project_service.delete_key_project(project_id)
    if not success:
        return jsonify({"message": "Key project not found."}), 404

    _clear_key_project_caches()
    return jsonify({"message": "Key project deleted successfully."}), 200

def _clear_key_project_caches():
    clear_cache_by_prefix("admin.api.key_project_list:")
    clear_cache_by_prefix("profile_ui_")

