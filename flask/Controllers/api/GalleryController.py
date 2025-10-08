from flask import request, jsonify
from Services.GalleryService import GalleryService
from Repositories.GalleryRepository import GalleryRepository
from config import SortOrder, SortOrderStr
import json

# Initialize Services
gallery_service = GalleryService(repository=GalleryRepository())

# -------------------Administrator Controller------------------------
# Gallery Controller
def gallery_list_route():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    order = SortOrder.DESC if request.args.get("order", "desc").upper() == SortOrderStr.DESC else SortOrder.ASC
    gallery_list, total_gallery = gallery_service.get_paginated_gallery_list(page, per_page, order)
    return jsonify({
        "gallery": [gallery.to_dict() for gallery in gallery_list],
        "total_gallery": total_gallery,
        "total_pages": (total_gallery + per_page - 1) // per_page,
    })

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
    return jsonify({"message": "Gallery added successfully", "gallery_id": gallery_id}), 201

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
        return jsonify({"message": "Gallery updated successfully"}), 200
    else:
        return jsonify({"message": "Failed to update gallery"}), 400

def delete_gallery_route(gallery_id):
    success = gallery_service.delete_gallery(gallery_id)
    if success:
        return jsonify({"message": "Gallery deleted successfully"}), 200
    else:
        return jsonify({"message": "Gallery not found"}), 404