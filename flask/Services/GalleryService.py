import uuid
from Repositories.Interfaces.IGalleryRepository import IGalleryRepository
from Models.Gallery import Gallery
from config import SortOrder
import tempfile, os
from constants.cloudinary import CloudinaryFolders, CloudinaryResourceType
from utils import cleanup_uploaded_files, upload_file_to_cloudinary

class GalleryService:
    def __init__(self, repository: IGalleryRepository):
        self.repository = repository

    # -------------------------- Gallery Service Methods -------------------------

    def get_gallery_by_id(self, gallery_id: str):
        return self.repository.get_gallery_by_id(gallery_id)

    def get_paginated_gallery_list(self, page, per_page, order: SortOrder = SortOrder.DESC):
        data, total_data = self.repository.get_paginated_gallery_list(page, per_page, order)
        system_info_list = [Gallery.from_dict(gallery) for gallery in data]
        return system_info_list, total_data

    def add_gallery(self, data: dict):
        if "id" not in data or not data["id"]:
            data["id"] = str(uuid.uuid4())

        gallery_url = None

        try:
            gallery_file = data.pop("gallery_file", None)
            if gallery_file:
                fd, path = tempfile.mkstemp()
                os.close(fd)
                gallery_file.save(path)

                gallery_url = upload_file_to_cloudinary(
                    path,
                    resource_type=CloudinaryResourceType.IMAGE,
                    folder=CloudinaryFolders.GALLERY
                )
                os.remove(path)

            data["image_url"] = gallery_url
            gallery = Gallery.from_dict(data)
            return self.repository.add_gallery(gallery)

        except Exception as e:
            cleanup_uploaded_files(gallery_url)
            raise e

    def update_gallery(self, gallery_id: str, data: dict):
        existing_gallery = self.get_gallery_by_id(gallery_id)
        if not existing_gallery:
            return False

        update_data = {
            "title": data.get("title") or existing_gallery["title"],
            "description": data.get("description") or existing_gallery["description"],
            "tags": data.get("tags") or existing_gallery["tags"],
        }

        new_gallery_url = None

        try:
            gallery_file = data.pop("gallery_file", None)
            if gallery_file:
                if existing_gallery.get("image_url"):
                    cleanup_uploaded_files(None, existing_gallery["image_url"])

                fd, path = tempfile.mkstemp()
                os.close(fd)
                gallery_file.save(path)

                new_gallery_url = upload_file_to_cloudinary(
                    path,
                    resource_type=CloudinaryResourceType.IMAGE,
                    folder=CloudinaryFolders.GALLERY
                )
                os.remove(path)

                update_data["image_url"] = new_gallery_url
            else:
                update_data["image_url"] = existing_gallery.get("image_url")

            update_data["id"] = existing_gallery.get("id") or str(uuid.uuid4())

            gallery = Gallery.from_dict(update_data)
            return self.repository.update_gallery(gallery_id, gallery)

        except Exception as e:
            cleanup_uploaded_files(new_gallery_url)
            raise e

    def delete_gallery(self, gallery_id: str):
        existing_gallery = self.get_gallery_by_id(gallery_id)
        if not existing_gallery:
            return False

        cleanup_uploaded_files(None, existing_gallery.get("image_url"))
        return self.repository.delete_gallery(gallery_id)

    def search_gallery_paginated(self, search_query, tags, locale, page, per_page, order):
        results, total = self.repository.search_gallery_paginated(search_query, tags, locale, page, per_page, order)
        gallery = [Gallery.from_dict(result) for result in results]

        return gallery, total

    def get_all_tags(self, limit: int = 50):
        return self.repository.get_all_tags(limit)