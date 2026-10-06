from flask import jsonify
from app.Services.GalleryService import GalleryService
from app.Repositories.GalleryRepository import GalleryRepository
from app.configurations import SortOrder, SortOrderStr
from app.Requests.api.GalleryRequest import GalleryRequest
from app.constants.messages import GALLERY_ADD_MSG, GALLERY_DELETE_MSG, GALLERY_NOT_FOUND_ERROR, GALLERY_UPDATE_ERROR, GALLERY_UPDATE_MSG
from app.utils import clear_cache_by_prefix

# Initialize Services
gallery_service = GalleryService(repository=GalleryRepository())

# -------------------Administrator Controller------------------------
# Gallery Controller
def gallery_list_route():
    form = GalleryRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    page = data["page"]
    per_page = data["per_page"]
    search_query = data["search_query"]
    order = data["order"]

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

    return jsonify(response_data)

def add_gallery_route():
    form = GalleryRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    gallery_id = gallery_service.add_gallery(data)
    clear_cache_by_prefix("gallery_")
    return jsonify({"message": GALLERY_ADD_MSG, "gallery_id": gallery_id}), 201

def update_gallery_route(gallery_id):
    form = GalleryRequest()
    data, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = gallery_service.update_gallery(gallery_id, data)
    if success:
        clear_cache_by_prefix("gallery_")
        return jsonify({"message": GALLERY_UPDATE_MSG}), 200
    else:
        return jsonify({"message": GALLERY_UPDATE_ERROR}), 400

def delete_gallery_route(gallery_id):
    form = GalleryRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    success = gallery_service.delete_gallery(gallery_id)
    if success:
        clear_cache_by_prefix("gallery_")
        return jsonify({"message": GALLERY_DELETE_MSG}), 200
    else:
        return jsonify({"message": GALLERY_NOT_FOUND_ERROR}), 404

