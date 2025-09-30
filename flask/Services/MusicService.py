import uuid
from Repositories.Interfaces.IMusicRepository import IMusicRepository
from Models.Music import Music
from config import SortOrder
import tempfile, os
from constants.cloudinary import CloudinaryFolders, CloudinaryResourceType
from utils import cleanup_uploaded_files, upload_file_to_cloudinary

class MusicService:
    def __init__(self, repository: IMusicRepository):
        self.repository = repository

    # -------------------------- Music Service Methods -------------------------

    def get_music_by_id(self, music_id: str):
        return self.repository.get_music_by_id(music_id)

    def get_paginated_music_list(self, page, per_page, order: SortOrder = SortOrder.DESC):
        data, total_data = self.repository.get_paginated_music_list(page, per_page, order)
        system_info_list = [Music.from_dict(music) for music in data]
        return system_info_list, total_data

    def add_music(self, data: dict):
        if "id" not in data or not data["id"]:
            data["id"] = str(uuid.uuid4())

        music_url, image_url = None, None

        try:
            music_file = data.pop("music_file", None)
            if music_file:
                fd, path = tempfile.mkstemp()
                os.close(fd)
                music_file.save(path)

                music_url = upload_file_to_cloudinary(
                    path,
                    resource_type=CloudinaryResourceType.AUDIO,
                    folder=CloudinaryFolders.MUSIC
                )
                os.remove(path)

            image_file = data.pop("image_file", None)
            if image_file:
                fd, path = tempfile.mkstemp()
                os.close(fd)
                image_file.save(path)

                image_url = upload_file_to_cloudinary(
                    path,
                    resource_type=CloudinaryResourceType.IMAGE,
                    folder=CloudinaryFolders.MUSIC
                )
                os.remove(path)

            data["url"] = music_url
            data["image"] = image_url

            music = Music(**data)
            return self.repository.add_music(music)

        except Exception as e:
            cleanup_uploaded_files(music_url, image_url)
            raise e

    def update_music(self, music_id: str, data: dict):
        existing_music = self.get_music_by_id(music_id)
        if not existing_music:
            return False

        update_data = {
            "title": data.get("title") or existing_music["title"],
            "artist": data.get("artist") or existing_music["artist"],
        }

        new_music_url, new_image_url = None, None

        try:
            music_file = data.pop("music_file", None)
            if music_file:
                if existing_music.get("url"):
                    cleanup_uploaded_files(existing_music["url"], None)

                fd, path = tempfile.mkstemp()
                os.close(fd)
                music_file.save(path)

                new_music_url = upload_file_to_cloudinary(
                    path,
                    resource_type=CloudinaryResourceType.AUDIO,
                    folder=CloudinaryFolders.MUSIC
                )
                os.remove(path)

                update_data["url"] = new_music_url
            else:
                update_data["url"] = existing_music.get("url")

            image_file = data.pop("image_file", None)
            if image_file:
                if existing_music.get("image"):
                    cleanup_uploaded_files(None, existing_music["image"])

                fd, path = tempfile.mkstemp()
                os.close(fd)
                image_file.save(path)

                new_image_url = upload_file_to_cloudinary(
                    path,
                    resource_type=CloudinaryResourceType.IMAGE,
                    folder=CloudinaryFolders.MUSIC
                )
                os.remove(path)

                update_data["image"] = new_image_url
            else:
                update_data["image"] = existing_music.get("image")

            update_data["id"] = existing_music.get("id") or str(uuid.uuid4())

            music = Music(**update_data)
            return self.repository.update_music(music_id, music)

        except Exception as e:
            cleanup_uploaded_files(new_music_url, new_image_url)
            raise e

    def delete_music(self, music_id: str):
        existing_music = self.get_music_by_id(music_id)
        if not existing_music:
            return False

        cleanup_uploaded_files(existing_music.get("url"), existing_music.get("image"))
        return self.repository.delete_music(music_id)

