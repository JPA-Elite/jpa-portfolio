from flask import request, jsonify
from Services.GalleryLikeService import GalleryLikeService
from Repositories.GalleryLikeRepository import GalleryLikeRepository
import json
from utils import clear_cache_by_prefix

# Initialize Services
gallery_like_service = GalleryLikeService(repository=GalleryLikeRepository())

# Gallery Like Controller
def add_gallery_like_route():
    gallery_id = request.form.get("gallery_id")
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if not gallery_id:
        return jsonify({"error": "Missing gallery_id"}), 400

    try:
        # Perform toggle logic (insert or update)
        result = gallery_like_service.toggle_gallery_like(
            gallery_id=json.loads(gallery_id),
            ip_address=client_ip
        )

        clear_cache_by_prefix("gallery_")
        return jsonify({
            "message": "Gallery like toggled successfully",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
