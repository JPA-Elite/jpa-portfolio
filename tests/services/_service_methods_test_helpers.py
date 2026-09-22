import importlib
import inspect
from contextlib import ExitStack
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask, session

from tests.test_support import VALID_OBJECT_ID


def _fake_user_agent():
    return SimpleNamespace(
        device=SimpleNamespace(family="Phone", brand="Brand", model="Model"),
        browser=SimpleNamespace(family="Chrome", version_string="1.0"),
        os=SimpleNamespace(family="Android", version_string="14"),
    )


def _base_existing_gallery():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "g-1",
        "title": {"en": "Gallery"},
        "description": {"en": "Desc"},
        "image_url": "/gallery.jpg",
        "tags": ["tag1"],
    }


def _base_existing_video():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "v-1",
        "title": {"en": "Video"},
        "description": {"en": "Desc"},
        "video_url": "/video.mp4",
        "tags": ["tag1"],
        "file": None,
    }


def _base_existing_music():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "m-1",
        "title": "Song",
        "artist": "Artist",
        "url": "/song.mp3",
        "image": "/cover.jpg",
        "duration": "1:23",
        "lyrics": "lyrics",
    }


def _base_existing_key_project():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "kp-1",
        "title": {"en": "Project"},
        "description": {"en": "Desc"},
        "stack": "Python",
        "status": "planned",
        "image_url": "/cover.jpg",
        "demo_url": "",
        "repo_url": "",
        "sort_order": 0,
        "is_active": True,
        "slides": [],
    }


def _base_existing_built_app():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "app-1",
        "slug": "taskflow",
        "platform": "Mobile",
        "version": "v1.2.0",
        "icon": "checkmark-done-outline",
        "name": {"en": "TaskFlow"},
        "short_description": {"en": "Task manager."},
        "full_description": {"en": ["Paragraph one.", "Paragraph two."]},
        "snapshots": [],
        "download_url": "#",
        "sort_order": 1,
        "is_active": True,
    }


def _base_existing_roadmap():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "cr-1",
        "company_name": "Company",
        "role_title": "Role",
        "period": "2024",
        "employment_type": "Internship",
        "location": "Cebu",
        "definition": "Definition",
        "summary": "Summary",
        "highlights": ["One"],
        "cover_image_url": "/cover.jpg",
        "activities": [],
        "accent_color": "#2962ff",
        "sort_order": 1,
        "is_active": True,
    }


def _comment_doc(id_key):
    return {
        "_id": VALID_OBJECT_ID,
        id_key: "item-1",
        "author_name": "user_127.0.0.1",
        "text": "hello",
        "ip_address": "127.0.0.1",
        "liked_ips": ["127.0.0.1"],
        "created_at": datetime.utcnow(),
    }


def _system_info_doc():
    return {
        "_id": VALID_OBJECT_ID,
        "system": "Windows",
        "node": "pc",
        "release": "11",
        "version": "1",
        "platform": "win",
        "architecture": "x64",
        "user_agent": "UA",
        "device": "Phone",
        "brand": "Brand",
        "model": "Model",
        "browser": "Chrome",
        "browser_version": "1.0",
        "os": "Windows",
        "os_version": "11",
        "page": "/profile",
        "timestamp": "01/01/2026 - 12:00 PM",
        "image_capture": None,
        "ip_address": "127.0.0.1",
        "city": "City",
        "region": "Region",
        "country": "PH",
        "location": "0,0",
    }


def _service_public_methods(service_cls):
    for name, fn in inspect.getmembers(service_cls, inspect.isfunction):
        if fn.__module__ != service_cls.__module__:
            continue
        if name == "__init__" or name.startswith("_"):
            continue
        yield name, fn


def _load_service_class(module_name: str, class_name: str):
    module = importlib.import_module(f"app.Services.{module_name}")
    return module, getattr(module, class_name)


def _build_service_instance(service_cls):
    service_name = service_cls.__name__

    repo = MagicMock(name=f"{service_name}Repository")
    attempt_repo = MagicMock(name="LoginAttemptRepository")

    for m in (
        "add_gallery", "add_video", "add_music", "add_key_project", "add_company_roadmap",
        "add_gallery_like", "add_vlog_like", "add_comment", "insert_portfolio", "insert_system_info",
        "add_built_app"
    ):
        getattr(repo, m).return_value = "new-id"

    for m in (
        "update_gallery", "update_video", "update_music", "update_key_project", "update_company_roadmap",
        "update_gallery_like", "update_vlog_like", "update_comment", "update_user",
        "delete_gallery", "delete_video", "delete_music", "delete_key_project", "delete_company_roadmap",
        "delete_login_attempt", "delete_system_info_by_id",
        "update_built_app", "delete_built_app"
    ):
        getattr(repo, m).return_value = True

    repo.get_paginated_gallery_list.return_value = ([_base_existing_gallery()], 1)
    repo.search_gallery_paginated.return_value = ([_base_existing_gallery()], 1)
    repo.get_gallery_by_id.return_value = _base_existing_gallery()
    repo.get_all_tags.return_value = ["tag1", "tag2"]

    repo.get_paginated_video_list.return_value = ([_base_existing_video()], 1)
    repo.search_video_paginated.return_value = ([_base_existing_video()], 1)
    repo.get_video_by_id.return_value = _base_existing_video()

    repo.get_paginated_music_list.return_value = ([_base_existing_music()], 1)
    repo.get_music_by_id.return_value = _base_existing_music()
    repo.get_music_by_url.return_value = _base_existing_music()

    repo.get_paginated_key_projects.return_value = ([_base_existing_key_project()], 1)
    repo.get_active_key_projects.return_value = [_base_existing_key_project()]
    repo.get_key_project_by_id.return_value = _base_existing_key_project()
    repo.count_key_projects.return_value = 1

    repo.get_paginated_company_roadmaps.return_value = ([_base_existing_roadmap()], 1)
    repo.get_active_company_roadmaps.return_value = [_base_existing_roadmap()]
    repo.get_company_roadmap_by_id.return_value = _base_existing_roadmap()
    repo.count_company_roadmaps.return_value = 1

    repo.get_paginated_built_apps.return_value = ([_base_existing_built_app()], 1)
    repo.get_active_built_apps.return_value = [_base_existing_built_app()]
    repo.get_built_app_by_id.return_value = _base_existing_built_app()
    repo.get_active_built_app_by_slug.return_value = _base_existing_built_app()
    repo.count_built_apps.return_value = 1
    repo.find.return_value = []

    repo.find__paginate_comments_by_gallery.return_value = [_comment_doc("gallery_id")]
    repo.count_comments_by_gallery.return_value = 1
    repo.find__paginate_comments_by_vlog.return_value = [_comment_doc("vlog_id")]
    repo.count_comments_by_vlog.return_value = 1
    repo.count_comments_by_vlog_ids.return_value = 1
    repo.find_by_id.return_value = {"_id": VALID_OBJECT_ID, "liked_ips": []}

    repo.get_gallery_likes_count_by_id.return_value = 1
    repo.get_gallery_likes_by_id_and_ip.return_value = {
        "_id": VALID_OBJECT_ID, "gallery_id": "g-1", "ip_address": "127.0.0.1", "like": True
    }
    repo.get_vlog_likes_count_by_id.return_value = 1
    repo.get_vlog_likes_counts_by_ids.return_value = {"v1": 1}
    repo.get_vlog_liked_states_by_ids_and_ip.return_value = {"v1": True}
    repo.get_vlog_likes_by_id_and_ip.return_value = {
        "_id": VALID_OBJECT_ID, "vlog_id": "v-1", "ip_address": "127.0.0.1", "like": True
    }

    repo.get_login_attempt_by_id.return_value = {"_id": "127.0.0.1", "attempts": 0, "lockout_until": None}
    repo.get_paginated_login_attempt_list.return_value = ([{"_id": "127.0.0.1", "attempts": 0, "lockout_until": None}], 1)

    repo.get_paginated_documents.return_value = ([_system_info_doc()], 1)
    repo.count_visits.return_value = 1
    repo.find_visit_for_day.return_value = None

    repo.find_by_username.return_value = {"_id": VALID_OBJECT_ID, "username": "admin", "password": "hashed"}
    repo.find_by_id.return_value = {"_id": VALID_OBJECT_ID, "username": "admin", "password": "hashed"}

    attempt_repo.get_attempt_info.return_value = {"attempts": 0, "lockout_until": None}
    attempt_repo.update_attempt.return_value = {"attempts": 0, "lockout_until": None}

    if service_name == "AuthService":
        return service_cls(repository=repo, attempt_repository=attempt_repo)
    return service_cls(repository=repo)


def _dummy_service_arg(service_name, method_name, param_name):
    if param_name in {"username"}:
        return "admin"
    if param_name in {"password"}:
        return "password123"
    if param_name in {"vlog_id", "gallery_id"}:
        return "item-1"
    if param_name == "comment_id":
        return VALID_OBJECT_ID
    if param_name == "music_id":
        return "music-1"
    if param_name == "video_id":
        return "video-1"
    if param_name == "project_id":
        return "project-1"
    if param_name == "roadmap_id":
        return "roadmap-1"
    if param_name == "app_id":
        return VALID_OBJECT_ID
    if param_name == "slug":
        return "taskflow"
    if param_name == "login_attempt_id":
        return "127.0.0.1"
    if param_name in {"page"}:
        return 1
    if param_name in {"per_page", "limit"}:
        return 5
    if param_name == "order":
        from app.configurations import SortOrder
        return SortOrder.ASC
    if param_name == "search_query":
        return "test"
    if param_name == "tags":
        return ["tag1"]
    if param_name == "locale":
        return "en"
    if param_name == "ip_address":
        return "127.0.0.1, 10.0.0.1"
    if param_name == "text":
        return "Hello"
    if param_name == "where_condition":
        return {}
    if param_name == "records":
        return [{"_id": VALID_OBJECT_ID, "image_capture": None}]
    if param_name == "cloudinary_url":
        return None
    if param_name == "ip":
        return "127.0.0.1"
    if param_name == "temp_path":
        return "dummy.mp3"
    if param_name == "vlog_ids":
        return ["v1", "v2"]
    if param_name == "gallery_ids":
        return ["g1", "g2"]

    if param_name == "data":
        if service_name == "GalleryService":
            if method_name == "add_gallery":
                return {"title": {"en": "Title"}, "description": {"en": "Desc"}, "tags": ["tag1"]}
            if method_name == "update_gallery":
                return {"title": {"en": "New"}, "description": {"en": "Desc"}, "tags": ["tag2"]}
        if service_name == "VideoService":
            if method_name == "add_video":
                return {"title": {"en": "Title"}, "description": {"en": "Desc"}, "tags": ["tag1"]}
            if method_name == "update_video":
                return {"title": {"en": "New"}, "description": {"en": "Desc"}, "tags": ["tag2"]}
        if service_name == "MusicService":
            if method_name == "add_music":
                return {"title": "Song", "artist": "Artist", "lyrics": "Lyrics"}
            if method_name == "update_music":
                return {"title": "Song 2", "artist": "Artist 2", "lyrics": "Updated lyrics"}
        if service_name == "KeyProjectService":
            if method_name == "add_key_project":
                return {"title": {"en": "Project"}, "description": {"en": "Desc"}, "stack": "Python", "status": "planned"}
            if method_name == "update_key_project":
                return {"title": {"en": "Updated"}, "description": {"en": "Desc"}}
        if service_name == "CompanyRoadmapService":
            if method_name == "add_company_roadmap":
                return {
                    "company_name": "Company",
                    "role_title": "Role",
                    "period": "2024",
                    "definition": "Definition",
                    "summary": "Summary",
                    "highlights": "One\\nTwo",
                }
            if method_name == "update_company_roadmap":
                return {"summary": "Updated"}
        if service_name == "BuiltAppService":
            if method_name == "add_built_app":
                return {
                    "name": {"en": "TaskFlow"},
                    "short_description": {"en": "Task manager."},
                    "full_description": {"en": ["Paragraph."]},
                    "platform": "Mobile",
                    "version": "v1.0.0",
                }
            if method_name == "update_built_app":
                return {"name": {"en": "TaskFlow Updated"}}
        if service_name in {"GalleryLikeService", "VlogLikeService"}:
            return {"ip_address": "127.0.0.1, 10.0.0.1", "gallery_id": "g-1", "vlog_id": "v-1", "like": True}
        return {}

    return "value"


def _patch_targets():
    return [
        ("app.Services.AuthService.check_password_hash", lambda *_args, **_kwargs: True),
        ("app.Services.AuthService.generate_password_hash", lambda value: f"hashed:{value}"),
        ("app.Services.GalleryService.cleanup_uploaded_files", lambda *a, **k: None),
        ("app.Services.GalleryService.convert_to_webp", lambda path: path),
        ("app.Services.GalleryService.upload_file_to_cloudinary", lambda *a, **k: "/uploaded.webp"),
        ("app.Services.VideoService.cleanup_uploaded_files", lambda *a, **k: None),
        ("app.Services.VideoService.upload_file_to_cloudinary", lambda *a, **k: "/uploaded.mp4"),
        ("app.Services.MusicService.cleanup_uploaded_files", lambda *a, **k: None),
        ("app.Services.MusicService.convert_to_webp", lambda path: path),
        ("app.Services.MusicService.upload_file_to_cloudinary", lambda *a, **k: "/uploaded"),
        ("app.Services.MusicService.MutagenFile", lambda *_a, **_k: SimpleNamespace(info=SimpleNamespace(length=61.2))),
        ("app.Services.KeyProjectService.cleanup_uploaded_files", lambda *a, **k: None),
        ("app.Services.KeyProjectService.convert_to_webp", lambda path: path),
        ("app.Services.KeyProjectService.upload_file_to_cloudinary", lambda *a, **k: "/uploaded.webp"),
        ("app.Services.CompanyRoadmapService.cleanup_uploaded_files", lambda *a, **k: None),
        ("app.Services.CompanyRoadmapService.convert_to_webp", lambda path: path),
        ("app.Services.CompanyRoadmapService.upload_file_to_cloudinary", lambda *a, **k: "/uploaded.webp"),
        ("app.Services.BuiltAppService.cleanup_uploaded_files", lambda *a, **k: None),
        ("app.Services.BuiltAppService.convert_to_webp", lambda path: path),
        ("app.Services.BuiltAppService.upload_file_to_cloudinary", lambda *a, **k: "/uploaded.webp"),
        ("app.Services.VisitService.delete_image_from_cloudinary", lambda *a, **k: None),
        ("app.Services.PortfolioService.parse", lambda *_a, **_k: _fake_user_agent()),
        ("app.Services.PortfolioService.requests.get", lambda *_a, **_k: SimpleNamespace(json=lambda: {})),
        ("app.Services.PortfolioService.pytz.timezone", lambda *_a, **_k: timezone.utc),
        ("app.Services.PortfolioService.platform.system", lambda: "Windows"),
        ("app.Services.PortfolioService.platform.node", lambda: "PC"),
        ("app.Services.PortfolioService.platform.release", lambda: "11"),
        ("app.Services.PortfolioService.platform.version", lambda: "Version"),
        ("app.Services.PortfolioService.platform.platform", lambda: "Windows"),
        ("app.Services.PortfolioService.platform.architecture", lambda: ("64bit", "")),
    ]


def run_service_methods_test(testcase, module_name: str, class_name: str):
    _module, service_cls = _load_service_class(module_name, class_name)
    service_name = service_cls.__name__

    app = Flask(__name__)
    app.secret_key = "test-secret"

    methods = list(_service_public_methods(service_cls))
    executed = []
    failures = []

    with ExitStack() as stack:
        for target, replacement in _patch_targets():
            stack.enter_context(patch(target, replacement))

        for method_name, method in methods:
            service = _build_service_instance(service_cls)
            sig = inspect.signature(method)
            args = []
            for param_name, param in list(sig.parameters.items())[1:]:
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue
                if param.default is not inspect._empty:
                    continue
                args.append(_dummy_service_arg(service_name, method_name, param_name))

            try:
                with app.test_request_context(
                    "/profile",
                    json={"username": "admin", "password": "secret"},
                    headers={"X-Forwarded-For": "127.0.0.1", "User-Agent": "Mozilla/5.0"},
                ):
                    session["user_id"] = VALID_OBJECT_ID
                    getattr(service, method_name)(*args)
                executed.append(method_name)
            except Exception as exc:
                failures.append(f"{service_name}.{method_name}: {exc}")

    if failures:
        testcase.fail("Service method execution failures:\\n" + "\\n".join(failures))

    testcase.assertEqual(
        len(executed),
        len(methods),
        f"Not all public methods executed for {service_name}: executed={len(executed)} methods={len(methods)}",
    )
