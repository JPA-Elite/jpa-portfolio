import uuid
from Repositories.Interfaces.IVideoRepository import IVideoRepository
from Models.Video import Video
from config import SortOrder
import tempfile, os
from constants.cloudinary import CloudinaryFolders, CloudinaryResourceType
from utils import cleanup_uploaded_files, upload_file_to_cloudinary

class VideoService:
    def __init__(self, repository: IVideoRepository):
        self.repository = repository

    # -------------------------- Video Service Methods -------------------------

    def get_video_by_id(self, video_id: str):
        return self.repository.get_video_by_id(video_id)

    def get_paginated_video_list(self, page, per_page, order: SortOrder = SortOrder.DESC):
        data, total_data = self.repository.get_paginated_video_list(page, per_page, order)
        system_info_list = [Video.from_dict(video) for video in data]
        return system_info_list, total_data

    def add_video(self, data: dict):
        if "id" not in data or not data["id"]:
            data["id"] = str(uuid.uuid4())

        video_url = None

        try:
            video_file = data.pop("video_file", None)
            if video_file:
                fd, path = tempfile.mkstemp()
                os.close(fd)
                video_file.save(path)

                video_url = upload_file_to_cloudinary(
                    path,
                    resource_type=CloudinaryResourceType.VIDEO,
                    folder=CloudinaryFolders.VIDEO
                )
                os.remove(path)

            data["video_url"] = video_url
            video = Video.from_dict(data)
            return self.repository.add_video(video)

        except Exception as e:
            cleanup_uploaded_files(video_url)
            raise e

    def update_video(self, video_id: str, data: dict):
        existing_video = self.get_video_by_id(video_id)
        if not existing_video:
            return False

        update_data = {
            "title": data.get("title") or existing_video["title"],
            "description": data.get("description") or existing_video["description"],
            "tags": data.get("tags") or existing_video["tags"],
        }

        new_video_url = None

        try:
            video_file = data.pop("video_file", None)
            if video_file:
                if existing_video.get("video_url"):
                    cleanup_uploaded_files(existing_video["video_url"], None)

                fd, path = tempfile.mkstemp()
                os.close(fd)
                video_file.save(path)

                new_video_url = upload_file_to_cloudinary(
                    path,
                    resource_type=CloudinaryResourceType.VIDEO,
                    folder=CloudinaryFolders.VIDEO
                )
                os.remove(path)

                update_data["video_url"] = new_video_url
            else:
                update_data["video_url"] = existing_video.get("video_url")

            update_data["id"] = existing_video.get("id") or str(uuid.uuid4())

            video = Video.from_dict(update_data)
            return self.repository.update_video(video_id, video)

        except Exception as e:
            cleanup_uploaded_files(new_video_url)
            raise e

    def delete_video(self, video_id: str):
        existing_video = self.get_video_by_id(video_id)
        if not existing_video:
            return False

        cleanup_uploaded_files(existing_video.get("video_url"))
        return self.repository.delete_video(video_id)

    def search_video_paginated(self, search_query, tags, locale, page, per_page, order):
        results, total = self.repository.search_video_paginated(search_query, tags, locale, page, per_page, order)
        gallery = [Video.from_dict(result) for result in results]

        return gallery, total

    def get_all_tags(self, limit: int = 50):
        return self.repository.get_all_tags(limit)

