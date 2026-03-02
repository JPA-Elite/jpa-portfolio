import os
import tempfile
import uuid

from Models.CompanyRoadmap import CompanyRoadmap
from Repositories.Interfaces.ICompanyRoadmapRepository import ICompanyRoadmapRepository
from configurations import SortOrder
from constants.cloudinary import CloudinaryFolders, CloudinaryResourceType
from utils import cleanup_uploaded_files, convert_to_webp, upload_file_to_cloudinary

_ROADMAP_I18N_LOCALES = ("en", "ceb", "fil_PH")


class CompanyRoadmapService:
    def __init__(self, repository: ICompanyRoadmapRepository):
        self.repository = repository

    def get_company_roadmap_by_id(self, roadmap_id: str):
        return self.repository.get_company_roadmap_by_id(roadmap_id)

    def get_paginated_company_roadmaps(self, page, per_page, order: SortOrder = SortOrder.DESC):
        data, total = self.repository.get_paginated_company_roadmaps(page, per_page, order)
        return [CompanyRoadmap.from_dict(item) for item in data], total

    def get_active_company_roadmaps(self):
        return [CompanyRoadmap.from_dict(item) for item in self.repository.get_active_company_roadmaps()]

    def add_company_roadmap(self, data: dict):
        if "id" not in data or not data["id"]:
            data["id"] = str(uuid.uuid4())

        data["highlights"] = self._normalize_highlights(data.get("highlights"))
        data["role_title_i18n"] = self._normalize_i18n_text_map(data.get("role_title_i18n"), data.get("role_title"))
        data["definition_i18n"] = self._normalize_i18n_text_map(data.get("definition_i18n"), data.get("definition"))
        data["summary_i18n"] = self._normalize_i18n_text_map(data.get("summary_i18n"), data.get("summary"))
        data["highlights_i18n"] = self._normalize_i18n_highlights_map(
            data.get("highlights_i18n"),
            data.get("highlights"),
        )
        data["accent_color"] = self._normalize_accent_color(data.get("accent_color"))

        cover_image_url = None
        uploaded_activity_urls = []

        try:
            cover_file = data.pop("cover_image_file", None)
            if cover_file:
                cover_image_url = self._upload_image_file(cover_file)

            activities = self._build_activities(
                activities_meta=data.pop("activities_meta", []),
                file_storage=data.pop("activity_files", None),
            )
            uploaded_activity_urls = [a.get("image_url") for a in activities if a.get("image_url")]

            data["cover_image_url"] = cover_image_url
            data["activities"] = activities

            roadmap = CompanyRoadmap.from_dict(data)
            return self.repository.add_company_roadmap(roadmap)
        except Exception:
            self._cleanup_image_url(cover_image_url)
            for url in uploaded_activity_urls:
                self._cleanup_image_url(url)
            raise

    def update_company_roadmap(self, roadmap_id: str, data: dict):
        existing = self.get_company_roadmap_by_id(roadmap_id)
        if not existing:
            return False

        update_data = {
            "id": existing.get("id") or str(uuid.uuid4()),
            "company_name": data.get("company_name") or existing.get("company_name", ""),
            "role_title": data.get("role_title") or existing.get("role_title", ""),
            "period": data.get("period") or existing.get("period", ""),
            "employment_type": data.get("employment_type") or existing.get("employment_type", "experience"),
            "location": data.get("location") if data.get("location") is not None else existing.get("location", ""),
            "role_title_i18n": self._merge_i18n_text_map(
                existing.get("role_title_i18n"),
                data.get("role_title_i18n"),
                data.get("role_title"),
                existing.get("role_title", ""),
            ),
            "definition": data.get("definition") if data.get("definition") is not None else existing.get("definition", ""),
            "definition_i18n": self._merge_i18n_text_map(
                existing.get("definition_i18n"),
                data.get("definition_i18n"),
                data.get("definition"),
                existing.get("definition", ""),
            ),
            "summary": data.get("summary") if data.get("summary") is not None else existing.get("summary", ""),
            "summary_i18n": self._merge_i18n_text_map(
                existing.get("summary_i18n"),
                data.get("summary_i18n"),
                data.get("summary"),
                existing.get("summary", ""),
            ),
            "highlights": (
                self._normalize_highlights(data.get("highlights"))
                if data.get("highlights") is not None
                else self._normalize_highlights(existing.get("highlights", []))
            ),
            "highlights_i18n": self._merge_i18n_highlights_map(
                existing.get("highlights_i18n"),
                data.get("highlights_i18n"),
                data.get("highlights"),
                existing.get("highlights", []),
            ),
            "accent_color": self._normalize_accent_color(
                data.get("accent_color") if data.get("accent_color") is not None else existing.get("accent_color")
            ),
            "sort_order": data.get("sort_order") if data.get("sort_order") is not None else existing.get("sort_order", 0),
            "is_active": data.get("is_active") if data.get("is_active") is not None else existing.get("is_active", True),
        }

        new_cover_image_url = None
        uploaded_activity_urls = []

        try:
            cover_file = data.pop("cover_image_file", None)
            current_cover = existing.get("cover_image_url")
            if cover_file:
                new_cover_image_url = self._upload_image_file(cover_file)
                update_data["cover_image_url"] = new_cover_image_url
                self._cleanup_image_url(current_cover)
            else:
                update_data["cover_image_url"] = current_cover

            activities_meta = data.pop("activities_meta", None)
            if activities_meta is None:
                update_data["activities"] = existing.get("activities", [])
            else:
                activities, uploaded_activity_urls = self._build_activities_for_update(
                    activities_meta=activities_meta,
                    file_storage=data.pop("activity_files", None),
                    existing_activities=existing.get("activities", []),
                )
                update_data["activities"] = activities

            roadmap = CompanyRoadmap.from_dict(update_data)
            return self.repository.update_company_roadmap(roadmap_id, roadmap)
        except Exception:
            self._cleanup_image_url(new_cover_image_url)
            for url in uploaded_activity_urls:
                self._cleanup_image_url(url)
            raise

    def delete_company_roadmap(self, roadmap_id: str):
        existing = self.get_company_roadmap_by_id(roadmap_id)
        if not existing:
            return False

        self._cleanup_image_url(existing.get("cover_image_url"))
        for activity in existing.get("activities", []) or []:
            self._cleanup_image_url((activity or {}).get("image_url"))

        return self.repository.delete_company_roadmap(roadmap_id)

    def seed_default_company_roadmaps_if_empty(self):
        if self.repository.count_company_roadmaps() > 0:
            return 0

        placeholder = "/static/images/no-project.png"
        seeded = [
            CompanyRoadmap.from_dict({
                "id": "cr-business-intern",
                "company_name": "Municipality of Vallehermoso",
                "role_title": "Business Intern",
                "period": "2019 - 2020",
                "employment_type": "Internship",
                "location": "Vallehermoso, Negros Oriental",
                "definition": "Foundational internship focused on practical office workflows, communication, and day-to-day business support tasks.",
                "summary": "This role helped build discipline in documentation, coordination, and problem-solving in a real workplace setting.",
                "highlights": [
                    "Supported day-to-day office tasks and documentation workflows.",
                    "Communicated with staff and learned formal workplace coordination.",
                    "Built early experience in structured problem solving.",
                ],
                "cover_image_url": placeholder,
                "activities": [
                    {"id": str(uuid.uuid4()), "sort_order": 0, "image_url": placeholder, "title": "Office Support", "caption": "Daily admin support and structured tasks."},
                    {"id": str(uuid.uuid4()), "sort_order": 1, "image_url": placeholder, "title": "Workflow Learning", "caption": "Learning business process flow and communication."},
                ],
                "accent_color": "#22c55e",
                "sort_order": 1,
                "is_active": True,
            }),
            CompanyRoadmap.from_dict({
                "id": "cr-trustarc-intern",
                "company_name": "TrustArc",
                "role_title": "Software Development Intern",
                "period": "2023",
                "employment_type": "Internship",
                "location": "Cebu City",
                "definition": "Software internship centered on secure API work, backend collaboration, and frontend integration in a professional development environment.",
                "summary": "Focused on safer API requests and cross-functional engineering tasks while learning production development practices.",
                "highlights": [
                    "Helped implement safe and secure API requests.",
                    "Worked with backend and frontend teams on product tasks.",
                    "Experienced enterprise development workflows and reviews.",
                ],
                "cover_image_url": placeholder,
                "activities": [
                    {"id": str(uuid.uuid4()), "sort_order": 0, "image_url": placeholder, "title": "API Tasks", "caption": "Working on secure API request flows."},
                    {"id": str(uuid.uuid4()), "sort_order": 1, "image_url": placeholder, "title": "Team Collaboration", "caption": "Collaborating across backend and frontend tasks."},
                ],
                "accent_color": "#7c3aed",
                "sort_order": 2,
                "is_active": True,
            }),
            CompanyRoadmap.from_dict({
                "id": "cr-chronostep-intern",
                "company_name": "Chronostep",
                "role_title": "Backend Development Intern",
                "period": "2023",
                "employment_type": "Internship",
                "location": "Cebu City",
                "definition": "Backend internship focused on internal projects and building maintainable features using Laravel and Vue in a client-driven environment.",
                "summary": "Contributed to internal systems while strengthening backend architecture and implementation skills.",
                "highlights": [
                    "Developed internal projects for company use.",
                    "Used Laravel and Vue for feature implementation.",
                    "Learned team-based development and delivery pace.",
                ],
                "cover_image_url": placeholder,
                "activities": [
                    {"id": str(uuid.uuid4()), "sort_order": 0, "image_url": placeholder, "title": "Internal Projects", "caption": "Building internal company tools and features."},
                    {"id": str(uuid.uuid4()), "sort_order": 1, "image_url": placeholder, "title": "Backend Workflow", "caption": "Laravel-based backend implementation and testing."},
                ],
                "accent_color": "#f59e0b",
                "sort_order": 3,
                "is_active": True,
            }),
            CompanyRoadmap.from_dict({
                "id": "cr-chronostep-engineer",
                "company_name": "Chronostep",
                "role_title": "Software Engineer",
                "period": "2024 - Present",
                "employment_type": "Full-time",
                "location": "Cebu City",
                "definition": "Full-time software engineering role building diverse client-focused solutions across backend, frontend, and integration requirements.",
                "summary": "Expanded from internship work into production delivery, handling broader responsibilities and multi-technology solutions.",
                "highlights": [
                    "Delivered client-specific projects using diverse technologies.",
                    "Worked across frontend, backend, and integration tasks.",
                    "Contributed to production-ready features and delivery timelines.",
                ],
                "cover_image_url": placeholder,
                "activities": [
                    {"id": str(uuid.uuid4()), "sort_order": 0, "image_url": placeholder, "title": "Client Delivery", "caption": "Shipping features for client requirements."},
                    {"id": str(uuid.uuid4()), "sort_order": 1, "image_url": placeholder, "title": "Engineering Work", "caption": "Multi-stack development and production support."},
                ],
                "accent_color": "#06b6d4",
                "sort_order": 4,
                "is_active": True,
            }),
        ]

        self.repository.add_many_company_roadmaps(seeded)
        return len(seeded)

    def _build_activities(self, activities_meta, file_storage):
        activities = []

        for index, activity_meta in enumerate(activities_meta or []):
            activity_meta = activity_meta or {}
            image_field = activity_meta.get("image_field")
            if not image_field:
                continue

            activity_file = file_storage.get(image_field) if file_storage else None
            if not activity_file:
                continue

            image_url = self._upload_image_file(activity_file)
            activities.append({
                "id": str(uuid.uuid4()),
                "sort_order": index,
                "image_url": image_url,
                "title": str(activity_meta.get("title") or "").strip(),
                "title_i18n": self._normalize_i18n_text_map(
                    activity_meta.get("title_i18n"),
                    activity_meta.get("title"),
                ),
                "caption": str(activity_meta.get("caption") or "").strip(),
                "caption_i18n": self._normalize_i18n_text_map(
                    activity_meta.get("caption_i18n"),
                    activity_meta.get("caption"),
                ),
            })

        return activities

    def _build_activities_for_update(self, activities_meta, file_storage, existing_activities):
        existing_activities = existing_activities or []
        existing_by_id = {
            str((item or {}).get("id")): item
            for item in existing_activities
            if (item or {}).get("id")
        }

        activities = []
        uploaded_urls = []
        kept_urls = set()
        cleaned_urls = set()

        for index, activity_meta in enumerate(activities_meta or []):
            activity_meta = activity_meta or {}
            activity_id = str(activity_meta.get("id") or "") or str(uuid.uuid4())
            previous = existing_by_id.get(activity_id, {})
            existing_image_url = activity_meta.get("existing_image_url") or previous.get("image_url")

            image_field = activity_meta.get("image_field")
            activity_file = file_storage.get(image_field) if (file_storage and image_field) else None

            if activity_file:
                image_url = self._upload_image_file(activity_file)
                uploaded_urls.append(image_url)
                if existing_image_url and existing_image_url != image_url:
                    self._cleanup_image_url(existing_image_url)
                    cleaned_urls.add(existing_image_url)
            else:
                image_url = existing_image_url
                if image_url:
                    kept_urls.add(image_url)

            if not image_url:
                continue

            activities.append({
                "id": activity_id,
                "sort_order": index,
                "image_url": image_url,
                "title": str(activity_meta.get("title") or previous.get("title") or "").strip(),
                "title_i18n": self._merge_i18n_text_map(
                    previous.get("title_i18n"),
                    activity_meta.get("title_i18n"),
                    activity_meta.get("title"),
                    previous.get("title", ""),
                ),
                "caption": str(activity_meta.get("caption") or previous.get("caption") or "").strip(),
                "caption_i18n": self._merge_i18n_text_map(
                    previous.get("caption_i18n"),
                    activity_meta.get("caption_i18n"),
                    activity_meta.get("caption"),
                    previous.get("caption", ""),
                ),
            })

        for previous in existing_activities:
            url = (previous or {}).get("image_url")
            if not url:
                continue
            still_present = any((a or {}).get("image_url") == url for a in activities)
            if not still_present and url not in kept_urls and url not in cleaned_urls:
                self._cleanup_image_url(url)

        return activities, uploaded_urls

    def _normalize_highlights(self, value):
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str):
            return [line.strip() for line in value.splitlines() if line.strip()]
        return []

    def _normalize_accent_color(self, value):
        color = str(value or "").strip()
        if not color:
            return "#2962ff"
        if not color.startswith("#"):
            color = f"#{color}"
        if len(color) not in (4, 7):
            return "#2962ff"
        return color

    def _normalize_i18n_text_map(self, value, fallback_en=""):
        normalized = {locale: "" for locale in _ROADMAP_I18N_LOCALES}
        fallback_text = str(fallback_en or "").strip()

        if isinstance(value, dict):
            for locale in _ROADMAP_I18N_LOCALES:
                normalized[locale] = str(value.get(locale, "") or "").strip()
        elif isinstance(value, str):
            normalized["en"] = value.strip()

        if fallback_text and not normalized["en"]:
            normalized["en"] = fallback_text

        if any(normalized.values()):
            return normalized
        return None

    def _normalize_i18n_highlights_map(self, value, fallback_en=None):
        normalized = {locale: [] for locale in _ROADMAP_I18N_LOCALES}

        if isinstance(value, dict):
            for locale in _ROADMAP_I18N_LOCALES:
                normalized[locale] = self._normalize_highlights(value.get(locale))
        elif isinstance(value, list):
            normalized["en"] = self._normalize_highlights(value)
        elif isinstance(value, str):
            normalized["en"] = self._normalize_highlights(value)

        fallback_list = self._normalize_highlights(fallback_en)
        if fallback_list and not normalized["en"]:
            normalized["en"] = fallback_list

        if any(normalized.values()):
            return normalized
        return None

    def _merge_i18n_text_map(self, existing_map, incoming_map, incoming_en_value=None, existing_en_value=""):
        base = self._normalize_i18n_text_map(existing_map, existing_en_value) or {
            locale: "" for locale in _ROADMAP_I18N_LOCALES
        }
        next_map = self._normalize_i18n_text_map(incoming_map, incoming_en_value)
        if not next_map:
            if incoming_en_value is not None:
                base["en"] = str(incoming_en_value or "").strip()
            return base if any(base.values()) else None

        merged = dict(base)
        for locale in _ROADMAP_I18N_LOCALES:
            if locale in next_map:
                merged[locale] = next_map.get(locale, "")

        if incoming_en_value is not None:
            merged["en"] = str(incoming_en_value or "").strip()

        return merged if any(merged.values()) else None

    def _merge_i18n_highlights_map(self, existing_map, incoming_map, incoming_en_value=None, existing_en_value=None):
        base = self._normalize_i18n_highlights_map(existing_map, existing_en_value) or {
            locale: [] for locale in _ROADMAP_I18N_LOCALES
        }
        next_map = self._normalize_i18n_highlights_map(incoming_map, incoming_en_value)
        if not next_map:
            if incoming_en_value is not None:
                base["en"] = self._normalize_highlights(incoming_en_value)
            return base if any(base.values()) else None

        merged = {locale: list(base.get(locale, [])) for locale in _ROADMAP_I18N_LOCALES}
        for locale in _ROADMAP_I18N_LOCALES:
            if locale in next_map:
                merged[locale] = self._normalize_highlights(next_map.get(locale))

        if incoming_en_value is not None:
            merged["en"] = self._normalize_highlights(incoming_en_value)

        return merged if any(merged.values()) else None

    def _upload_image_file(self, image_file):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        image_file.save(path)

        webp_path = convert_to_webp(path)
        try:
            return upload_file_to_cloudinary(
                webp_path,
                resource_type=CloudinaryResourceType.IMAGE,
                folder=CloudinaryFolders.ROADMAP,
            )
        finally:
            if os.path.exists(path):
                os.remove(path)
            if webp_path != path and os.path.exists(webp_path):
                os.remove(webp_path)

    def _cleanup_image_url(self, url):
        if not url or "res.cloudinary.com" not in str(url):
            return
        cleanup_uploaded_files(None, url)
