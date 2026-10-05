import os
import re
import tempfile
import uuid
from flask import current_app
from app.Models.BuiltApp import BuiltApp
from app.Repositories.Interfaces.IBuiltAppRepository import IBuiltAppRepository
from app.configurations import SortOrder
from app.constants.built_apps import BUILT_APPS
from app.constants.cloudinary import CloudinaryFolders, CloudinaryResourceType
from app.utils import cleanup_uploaded_files, convert_to_webp, upload_file_to_cloudinary


class BuiltAppService:
    def __init__(self, repository: IBuiltAppRepository):
        self.repository = repository

    def get_built_app_by_id(self, app_id: str):
        return self.repository.get_built_app_by_id(app_id)

    def get_paginated_built_apps(
        self,
        page,
        per_page,
        order: SortOrder = SortOrder.DESC,
        search_query: str = "",
        platform_filter: str = "",
        is_active_filter=None,
    ):
        data, total = self.repository.get_paginated_built_apps(
            page,
            per_page,
            order,
            search_query,
            platform_filter=platform_filter,
            is_active_filter=is_active_filter,
        )
        return [BuiltApp.from_dict(item) for item in data], total

    def get_active_built_apps(self):
        return [BuiltApp.from_dict(item) for item in self.repository.get_active_built_apps()]

    def get_active_built_app_by_slug(self, slug: str):
        item = self.repository.find_active_built_app_by_slug(slug)
        return BuiltApp.from_dict(item) if item else None

    def add_built_app(self, data: dict):
        if "id" not in data or not data["id"]:
            data["id"] = str(uuid.uuid4())

        base_slug = self._normalize_slug(
            data.get("slug")
            or ((data.get("name") or {}).get("en") or "")
        )
        data["slug"] = self._ensure_unique_slug(base_slug)

        uploaded_urls = []
        try:
            icon_image_file = data.pop("icon_image_file", None)
            if icon_image_file:
                icon_image_url = self._upload_snapshot_file(icon_image_file)
                uploaded_urls.append(icon_image_url)
                data["icon_image_url"] = icon_image_url
            data["snapshots"] = self._build_new_snapshots(
                data.pop("snapshot_files", None),
                uploaded_urls,
            )
            built_app = BuiltApp.from_dict(data)
            return self.repository.add_built_app(built_app)
        except Exception:
            for url in uploaded_urls:
                self._cleanup_image_url(url)
            raise

    def update_built_app(self, app_id: str, data: dict):
        existing = self.get_built_app_by_id(app_id)
        if not existing:
            return False

        name = data.get("name") or existing.get("name", {})
        short_description = data.get("short_description") or existing.get("short_description", {})
        full_description = data.get("full_description") or existing.get("full_description", {})

        requested_slug = str(data.get("slug") or "").strip()
        current_slug = existing.get("slug", "")
        if requested_slug:
            normalized = self._normalize_slug(requested_slug)
            if normalized != current_slug:
                new_slug = self._ensure_unique_slug(normalized, exclude_id=app_id)
            else:
                new_slug = current_slug
        else:
            new_slug = current_slug or self._ensure_unique_slug(self._normalize_slug((name or {}).get("en") or ""))

        update_data = {
            "id": existing.get("id") or str(uuid.uuid4()),
            "slug": new_slug,
            "name": name,
            "short_description": short_description,
            "full_description": full_description,
            "platform": data.get("platform") or existing.get("platform", "Mobile"),
            "version": data.get("version") if data.get("version") is not None else existing.get("version", ""),
            "icon": data.get("icon") if data.get("icon") is not None else existing.get("icon", "apps-outline"),
            "icon_image_url": existing.get("icon_image_url", ""),
            "download_url": data.get("download_url") if data.get("download_url") is not None else existing.get("download_url", ""),
            "sort_order": data.get("sort_order") if data.get("sort_order") is not None else existing.get("sort_order", 0),
            "is_active": data.get("is_active") if data.get("is_active") is not None else existing.get("is_active", True),
        }

        snapshots_meta = data.pop("snapshots_meta", None)
        uploaded_urls = []

        try:
            icon_image_file = data.pop("icon_image_file", None)
            if icon_image_file:
                new_icon_image_url = self._upload_snapshot_file(icon_image_file)
                uploaded_urls.append(new_icon_image_url)
                update_data["icon_image_url"] = new_icon_image_url
                self._cleanup_image_url(existing.get("icon_image_url", ""))

            if snapshots_meta is None:
                update_data["snapshots"] = existing.get("snapshots", [])
            else:
                snapshots, uploaded_urls = self._build_snapshots_for_update(
                    snapshots_meta=snapshots_meta,
                    file_storage=data.pop("snapshot_files", None),
                    existing_snapshots=existing.get("snapshots", []),
                )
                update_data["snapshots"] = snapshots

            return self.repository.update_built_app(app_id, BuiltApp.from_dict(update_data))
        except Exception:
            for url in uploaded_urls:
                self._cleanup_image_url(url)
            raise

    def delete_built_app(self, app_id: str):
        existing = self.get_built_app_by_id(app_id)
        if not existing:
            return False

        for snapshot in existing.get("snapshots", []):
            url = (snapshot or {}).get("image_url")
            if url:
                self._cleanup_image_url(url)
        self._cleanup_image_url(existing.get("icon_image_url", ""))
        return self.repository.delete_built_app(app_id)

    def seed_default_built_apps_if_empty(self):
        from app.Services.SeedService import SeedService
        return SeedService.ensure_seeded(
            self.repository.count_built_apps,
            self._seed_default_built_apps,
        )

    def _seed_default_built_apps(self):
        seeded = []
        for index, row in enumerate(BUILT_APPS, start=1):
            seeded.append(BuiltApp.from_dict({
                "id": f"app-{row['slug']}",
                "slug": row["slug"],
                "name": self._same_text(row["name"]),
                "short_description": self._same_text(row["short_description"]),
                "full_description": self._same_paragraphs(row["full_description"]),
                "platform": row["platform"],
                "version": row["version"],
                "icon": row["icon"],
                "icon_image_url": row.get("icon_image_url", ""),
                "snapshots": [],
                "download_url": row.get("download_url", "#"),
                "sort_order": index,
                "is_active": True,
            }))

        self.repository.add_many_built_apps(seeded)
        return len(seeded)

    def _build_new_snapshots(self, file_storage, uploaded_urls):
        files = file_storage.getlist("snapshot_files") if file_storage else []
        snapshots = []
        for file in files:
            if not file:
                continue
            url = self._upload_snapshot_file(file)
            uploaded_urls.append(url)
            snapshots.append({
                "id": str(uuid.uuid4()),
                "sort_order": len(snapshots),
                "image_url": url,
            })
        return snapshots

    def _build_snapshots_for_update(self, snapshots_meta, file_storage, existing_snapshots):
        existing_snapshots = existing_snapshots or []
        existing_by_id = {
            str((snapshot or {}).get("id")): snapshot
            for snapshot in existing_snapshots
            if (snapshot or {}).get("id")
        }

        snapshots = []
        uploaded_urls = []

        for index, meta in enumerate(snapshots_meta or []):
            meta = meta or {}
            meta_id = str(meta.get("id") or "")

            if meta.get("remove"):
                previous = existing_by_id.get(meta_id, {})
                removed_url = (previous or {}).get("image_url")
                if removed_url:
                    self._cleanup_image_url(removed_url)
                continue

            image_field = meta.get("image_field")
            snapshot_file = file_storage.get(image_field) if (file_storage and image_field) else None

            if snapshot_file:
                url = self._upload_snapshot_file(snapshot_file)
                uploaded_urls.append(url)

                previous = existing_by_id.get(meta_id, {})
                old_url = (previous or {}).get("image_url")
                if old_url:
                    self._cleanup_image_url(old_url)
            elif meta_id and meta_id in existing_by_id:
                url = existing_by_id[meta_id].get("image_url")
            else:
                continue

            if not url:
                continue

            snapshots.append({
                "id": meta_id or str(uuid.uuid4()),
                "sort_order": len(snapshots),
                "image_url": url,
            })

        for snapshot in existing_snapshots:
            url = (snapshot or {}).get("image_url")
            if not url:
                continue
            still_present = any((s or {}).get("image_url") == url for s in snapshots)
            if not still_present:
                self._cleanup_image_url(url)

        return snapshots, uploaded_urls

    def _upload_snapshot_file(self, snapshot_file):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        snapshot_file.save(path)

        webp_path = convert_to_webp(path)
        try:
            return upload_file_to_cloudinary(
                webp_path,
                resource_type=CloudinaryResourceType.IMAGE,
                folder=CloudinaryFolders.BUILT_APPS,
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

    def _normalize_slug(self, value):
        slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
        return slug or f"app-{uuid.uuid4().hex[:6]}"

    def _ensure_unique_slug(self, base_slug, exclude_id=None):
        candidates = self.repository.find_by_slug_like(base_slug)
        taken = set()
        for item in candidates:
            if exclude_id and str(item.get("_id")) == str(exclude_id):
                continue
            taken.add(str(item.get("slug", "")).lower())

        if base_slug.lower() not in taken:
            return base_slug

        counter = 2
        while f"{base_slug}-{counter}".lower() in taken:
            counter += 1
        return f"{base_slug}-{counter}"

    def _same_text(self, text):
        return {
            "en": text,
            "ceb": text,
            "fr": text,
            "fil_PH": text,
        }

    def _same_paragraphs(self, paragraphs):
        paragraphs = [str(p).strip() for p in (paragraphs or []) if str(p).strip()]
        return {
            "en": paragraphs,
            "ceb": list(paragraphs),
            "fr": list(paragraphs),
            "fil_PH": list(paragraphs),
        }
