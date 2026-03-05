from flask import request, jsonify
from backend.Services.GalleryService import GalleryService
from backend.Repositories.GalleryRepository import GalleryRepository
from backend.configurations import SortOrder, SortOrderStr
import json
from backend.constants.messages import GALLERY_ADD_MSG, GALLERY_DELETE_MSG, GALLERY_NOT_FOUND_ERROR, GALLERY_UPDATE_ERROR, GALLERY_UPDATE_MSG
from backend.utils import clear_cache_by_prefix, get_cache_data
from backend.extensions import cache

# Initialize Services
gallery_service = GalleryService(repository=GalleryRepository())

# -------------------Administrator Controller------------------------
# Gallery Controller
def gallery_list_route():
    cached_data, cache_key = get_cache_data("admin.api.gallery_list", request.args)
    if cached_data:
        return jsonify(cached_data)

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search_query = (request.args.get("search") or "").strip()
    order = SortOrder.DESC if request.args.get("order", "desc").upper() == SortOrderStr.DESC else SortOrder.ASC
    if search_query:
        gallery_list, total_gallery = gallery_service.search_gallery_paginated(
            search_query,
            None,
            "en",
            page,
            per_page,
            order,
        )
    else:
        gallery_list, total_gallery = gallery_service.get_paginated_gallery_list(page, per_page, order)

    response_data = {
        "gallery": [gallery.to_dict() for gallery in gallery_list],
        "total_gallery": total_gallery,
        "total_pages": (total_gallery + per_page - 1) // per_page,
        "search": search_query,
    }

    cache.set(cache_key, response_data, timeout=300)
    return jsonify(response_data)

def add_gallery_route():
    title = request.form.get("title")
    description = request.form.get("description")
    gallery_file = request.files.get("image_file")
    tags = request.form.get("tags")
    # Pass raw request data + files to service
    data = {
        "title": json.loads(title) if title else {},
        "description": json.loads(description) if description else {},
        "gallery_file": gallery_file,
        "tags": json.loads(tags) if tags else [],
    }

    gallery_id = gallery_service.add_gallery(data)
    clear_cache_by_prefix("admin.api.gallery_list:")
    clear_cache_by_prefix("gallery_")
    return jsonify({"message": GALLERY_ADD_MSG, "gallery_id": gallery_id}), 201

def update_gallery_route(gallery_id):
    title = request.form.get("title")
    description = request.form.get("description")
    gallery_file = request.files.get("image_file")
    tags = request.form.get("tags")

    update_data = {
        "title": json.loads(title) if title else {},
        "description": json.loads(description) if description else {},
        "gallery_file": gallery_file,
        "tags": json.loads(tags) if tags else [],
    }

    success = gallery_service.update_gallery(gallery_id, update_data)
    if success:
        clear_cache_by_prefix("admin.api.gallery_list:")
        clear_cache_by_prefix("gallery_")
        return jsonify({"message": GALLERY_UPDATE_MSG}), 200
    else:
        return jsonify({"message": GALLERY_UPDATE_ERROR}), 400

def delete_gallery_route(gallery_id):
    success = gallery_service.delete_gallery(gallery_id)
    if success:
        clear_cache_by_prefix("admin.api.gallery_list:")
        clear_cache_by_prefix("gallery_")
        return jsonify({"message": GALLERY_DELETE_MSG}), 200
    else:
        return jsonify({"message": GALLERY_NOT_FOUND_ERROR}), 404
