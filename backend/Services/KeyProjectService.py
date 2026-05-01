import os
import tempfile
import uuid

from flask import current_app

from backend.Models.KeyProject import KeyProject
from backend.Repositories.Interfaces.IKeyProjectRepository import IKeyProjectRepository
from backend.configurations import SortOrder
from backend.constants.cloudinary import CloudinaryFolders, CloudinaryResourceType
from backend.utils import cleanup_uploaded_files, convert_to_webp, upload_file_to_cloudinary


class KeyProjectService:
    def __init__(self, repository: IKeyProjectRepository):
        self.repository = repository

    def get_key_project_by_id(self, project_id: str):
        return self.repository.get_key_project_by_id(project_id)

    def get_paginated_key_projects(
        self,
        page,
        per_page,
        order: SortOrder = SortOrder.DESC,
        search_query: str = "",
        status_filter: str = "",
        is_active_filter=None,
    ):
        data, total = self.repository.get_paginated_key_projects(
            page,
            per_page,
            order,
            search_query,
            status_filter=status_filter,
            is_active_filter=is_active_filter,
        )
        return [KeyProject.from_dict(item) for item in data], total

    def get_active_key_projects(self):
        return [KeyProject.from_dict(item) for item in self.repository.get_active_key_projects()]

    def add_key_project(self, data: dict):
        if "id" not in data or not data["id"]:
            data["id"] = str(uuid.uuid4())

        image_url = None
        uploaded_slide_urls = []

        try:
            image_file = data.pop("image_file", None)
            if image_file:
                image_url = self._upload_image_file(image_file)

            slides = self._build_additional_slides(
                slides_meta=data.pop("slides_meta", []),
                file_storage=data.pop("slide_files", None),
            )
            uploaded_slide_urls = [s.get("image_url") for s in slides if s.get("image_url")]

            data["image_url"] = image_url
            data["slides"] = slides
            key_project = KeyProject.from_dict(data)
            return self.repository.add_key_project(key_project)
        except Exception:
            self._cleanup_image_url(image_url)
            for slide_url in uploaded_slide_urls:
                self._cleanup_image_url(slide_url)
            raise

    def update_key_project(self, project_id: str, data: dict):
        existing = self.get_key_project_by_id(project_id)
        if not existing:
            return False

        update_data = {
            "title": data.get("title") or existing.get("title", {}),
            "description": data.get("description") or existing.get("description", {}),
            "stack": data.get("stack") if data.get("stack") is not None else existing.get("stack", ""),
            "status": data.get("status") or existing.get("status", "shipped"),
            "demo_url": data.get("demo_url") if data.get("demo_url") is not None else existing.get("demo_url", ""),
            "repo_url": data.get("repo_url") if data.get("repo_url") is not None else existing.get("repo_url", ""),
            "sort_order": data.get("sort_order") if data.get("sort_order") is not None else existing.get("sort_order", 0),
            "is_active": data.get("is_active") if data.get("is_active") is not None else existing.get("is_active", True),
            "id": existing.get("id") or str(uuid.uuid4()),
        }

        new_cover_image_url = None
        uploaded_slide_urls = []

        try:
            image_file = data.pop("image_file", None)
            current_cover = existing.get("image_url")
            if image_file:
                new_cover_image_url = self._upload_image_file(image_file)
                update_data["image_url"] = new_cover_image_url
                self._cleanup_image_url(current_cover)
            else:
                update_data["image_url"] = current_cover

            slides_meta = data.pop("slides_meta", None)
            if slides_meta is None:
                update_data["slides"] = existing.get("slides", [])
            else:
                slides, uploaded_slide_urls = self._build_additional_slides_for_update(
                    slides_meta=slides_meta,
                    file_storage=data.pop("slide_files", None),
                    existing_slides=existing.get("slides", []),
                )
                update_data["slides"] = slides

            key_project = KeyProject.from_dict(update_data)
            return self.repository.update_key_project(project_id, key_project)
        except Exception:
            self._cleanup_image_url(new_cover_image_url)
            for slide_url in uploaded_slide_urls:
                self._cleanup_image_url(slide_url)
            raise

    def delete_key_project(self, project_id: str):
        existing = self.get_key_project_by_id(project_id)
        if not existing:
            return False

        self._cleanup_image_url(existing.get("image_url"))
        for slide in existing.get("slides", []):
            self._cleanup_image_url((slide or {}).get("image_url"))
        return self.repository.delete_key_project(project_id)

    def seed_default_projects_if_empty(self):
        if self.repository.count_key_projects() > 0:
            return 0

        defaults = self._default_project_seed_data()
        seeded = []
        for row in defaults:
            image_url = row.get("image_url")
            local_image_name = row.pop("local_image_name", None)

            if local_image_name:
                local_path = os.path.join(current_app.root_path, "static", "images", local_image_name)
                if os.path.exists(local_path):
                    try:
                        image_url = upload_file_to_cloudinary(
                            local_path,
                            resource_type=CloudinaryResourceType.IMAGE,
                            folder=CloudinaryFolders.PROJECT,
                        )
                    except Exception as exc:
                        current_app.logger.warning(
                            "Cloudinary upload failed for key project seed '%s': %s",
                            row.get("title", {}).get("en", "unknown"),
                            exc,
                        )
                        image_url = f"/static/images/{local_image_name}"

            row["image_url"] = image_url
            row.setdefault("slides", [])
            seeded.append(KeyProject.from_dict(row))

        self.repository.add_many_key_projects(seeded)
        return len(seeded)

    def _build_additional_slides(self, slides_meta, file_storage):
        slides = []
        uploaded_urls = []

        for index, slide_meta in enumerate(slides_meta or []):
            image_field = (slide_meta or {}).get("image_field")
            if not image_field:
                continue

            slide_file = file_storage.get(image_field) if file_storage else None
            if not slide_file:
                continue

            image_url = self._upload_image_file(slide_file)
            uploaded_urls.append(image_url)

            slides.append({
                "id": str(uuid.uuid4()),
                "sort_order": index,
                "image_url": image_url,
                "title": self._localized_map(slide_meta.get("title")),
                "description": self._localized_map(slide_meta.get("description")),
            })

        return slides

    def _build_additional_slides_for_update(self, slides_meta, file_storage, existing_slides):
        existing_slides = existing_slides or []
        existing_by_id = {
            str((slide or {}).get("id")): slide
            for slide in existing_slides
            if (slide or {}).get("id")
        }

        slides = []
        uploaded_urls = []
        kept_existing_urls = set()
        cleaned_urls = set()

        for index, slide_meta in enumerate(slides_meta or []):
            slide_meta = slide_meta or {}
            slide_id = str(slide_meta.get("id") or "") or str(uuid.uuid4())
            previous = existing_by_id.get(slide_id, {})
            existing_image_url = slide_meta.get("existing_image_url") or previous.get("image_url")

            image_field = slide_meta.get("image_field")
            slide_file = file_storage.get(image_field) if (file_storage and image_field) else None

            if slide_file:
                image_url = self._upload_image_file(slide_file)
                uploaded_urls.append(image_url)
                # remove replaced image only after successful new upload
                if existing_image_url and existing_image_url != image_url:
                    self._cleanup_image_url(existing_image_url)
                    cleaned_urls.add(existing_image_url)
            else:
                image_url = existing_image_url
                if image_url:
                    kept_existing_urls.add(image_url)

            if not image_url:
                continue

            slides.append({
                "id": slide_id,
                "sort_order": index,
                "image_url": image_url,
                "title": self._localized_map(slide_meta.get("title"), previous.get("title")),
                "description": self._localized_map(slide_meta.get("description"), previous.get("description")),
            })

        # remove deleted slides (present before, absent now)
        for slide in existing_slides:
            url = (slide or {}).get("image_url")
            if not url:
                continue
            still_present = any((s or {}).get("image_url") == url for s in slides)
            if not still_present and url not in kept_existing_urls and url not in cleaned_urls:
                self._cleanup_image_url(url)

        return slides, uploaded_urls

    def _upload_image_file(self, image_file):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        image_file.save(path)

        webp_path = convert_to_webp(path)
        try:
            image_url = upload_file_to_cloudinary(
                webp_path,
                resource_type=CloudinaryResourceType.IMAGE,
                folder=CloudinaryFolders.PROJECT,
            )
            return image_url
        finally:
            if os.path.exists(path):
                os.remove(path)
            if webp_path != path and os.path.exists(webp_path):
                os.remove(webp_path)

    def _cleanup_image_url(self, url):
        if not url or "res.cloudinary.com" not in str(url):
            return
        cleanup_uploaded_files(None, url)

    def _localized_map(self, value, fallback=None):
        if isinstance(value, dict):
            normalized = {
                "en": (value.get("en") or "").strip(),
                "ceb": (value.get("ceb") or "").strip(),
                "fr": (value.get("fr") or "").strip(),
                "fil_PH": (value.get("fil_PH") or "").strip(),
            }
            if any(normalized.values()):
                return normalized

        if isinstance(value, str):
            text = value.strip()
            if text:
                return {
                    "en": text,
                    "ceb": text,
                    "fr": text,
                    "fil_PH": text,
                }

        if isinstance(fallback, dict):
            return {
                "en": (fallback.get("en") or "").strip(),
                "ceb": (fallback.get("ceb") or "").strip(),
                "fr": (fallback.get("fr") or "").strip(),
                "fil_PH": (fallback.get("fil_PH") or "").strip(),
            }

        return {
            "en": "",
            "ceb": "",
            "fr": "",
            "fil_PH": "",
        }

    def _default_project_seed_data(self):
        same_title = lambda text: {"en": text, "ceb": text, "fr": text, "fil_PH": text}
        same_desc = lambda text: {"en": text, "ceb": text, "fr": text, "fil_PH": text}

        return [
            {
                "id": "kp-jaom-connect",
                "title": same_title("JAOM-CONNECT"),
                "description": same_desc("Community platform project with Angular and Laravel featuring user flows, content pages, and admin-ready backend integrations."),
                "stack": "Angular • Laravel",
                "status": "shipped",
                "local_image_name": "jaom.webp",
                "demo_url": "",
                "repo_url": "",
                "sort_order": 1,
                "is_active": True,
                "slides": [],
            },
            {
                "id": "kp-ai-voice",
                "title": same_title("AI Voice Recognition"),
                "description": same_desc("Experimental Python project focused on speech recognition workflows and audio-processing exploration."),
                "stack": "Python",
                "status": "building",
                "local_image_name": "no-project.webp",
                "demo_url": "",
                "repo_url": "",
                "sort_order": 2,
                "is_active": True,
                "slides": [],
            },
            {
                "id": "kp-billing-gpay",
                "title": same_title("BillingSolution-G-Pay"),
                "description": same_desc("Laravel-based billing workflow prototype for payment-oriented business operations and tracking."),
                "stack": "Laravel",
                "status": "shipped",
                "local_image_name": "no-project.webp",
                "demo_url": "",
                "repo_url": "",
                "sort_order": 3,
                "is_active": True,
                "slides": [],
            },
            {
                "id": "kp-tourist-booking",
                "title": same_title("TouristSpot Booking System"),
                "description": same_desc("Booking management system concept for tourism reservations, schedules, and customer interactions."),
                "stack": "Laravel",
                "status": "shipped",
                "local_image_name": "no-project.webp",
                "demo_url": "",
                "repo_url": "",
                "sort_order": 4,
                "is_active": True,
                "slides": [],
            },
            {
                "id": "kp-tech-booking",
                "title": same_title("Technician Booking System"),
                "description": same_desc("Service booking flow prototype connecting customers with technicians through structured scheduling."),
                "stack": "Angular • Laravel",
                "status": "building",
                "local_image_name": "no-project.webp",
                "demo_url": "",
                "repo_url": "",
                "sort_order": 5,
                "is_active": True,
                "slides": [],
            },
            {
                "id": "kp-socio-fanline",
                "title": same_title("Socio-Fanline"),
                "description": same_desc("Frontend-focused concept project exploring social-style UI layouts and presentation design."),
                "stack": "HTML • CSS",
                "status": "planned",
                "local_image_name": "no-project.webp",
                "demo_url": "",
                "repo_url": "",
                "sort_order": 6,
                "is_active": True,
                "slides": [],
            },
        ]
