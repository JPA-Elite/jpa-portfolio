import importlib
import inspect
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask, Response

from app.Repositories.BaseRepository import BaseRepository
from tests.test_support import VALID_OBJECT_ID


class _DummyModel:
    def __init__(self, data):
        self._data = dict(data)

    def to_dict(self):
        return dict(self._data)


class _DummyHTTPResponse:
    def __init__(self):
        self.status_code = 200
        self.headers = {"Content-Type": "audio/mpeg"}
        self.raw = SimpleNamespace(headers={"Content-Type": "audio/mpeg"})

    def json(self):
        return {"country": "PH", "loc": "0,0"}

    def iter_content(self, chunk_size=4096):
        yield b"x" * min(chunk_size, 16)


class _DummyRedirectResponse:
    def __init__(self, location="/mock"):
        self.location = location
        self.headers = {}
        self.status_code = 302

    def set_cookie(self, key, value="", *args, **kwargs):
        self.headers[f"Set-Cookie-{key}"] = value


class _DummyForm:
    def __init__(self):
        self.username = SimpleNamespace(data="admin")
        self.password = SimpleNamespace(data="secret")
        self.remember = SimpleNamespace(data=False)

    def validate_on_submit(self):
        return False


def _fake_get_mongo_client(self, collection_name):
    return object(), {"name": "fake_db"}, SimpleNamespace(name=collection_name)


def _gallery_doc():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "g1",
        "title": {"en": "Gallery"},
        "description": {"en": "Description"},
        "image_url": "/img.jpg",
        "tags": ["tag1"],
    }


def _video_doc():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "v1",
        "title": {"en": "Video"},
        "description": {"en": "Description"},
        "video_url": "/video.mp4",
        "file": None,
        "tags": ["tag1"],
    }


def _music_doc():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "m1",
        "title": "Song",
        "artist": "Artist",
        "url": "/song.mp3",
        "image": "/cover.jpg",
        "duration": "1:23",
        "lyrics": "Lyrics",
    }


def _key_project_doc():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "kp1",
        "title": {"en": "Project"},
        "description": {"en": "Description"},
        "stack": "Python",
        "status": "planned",
        "image_url": "/cover.jpg",
        "demo_url": "",
        "repo_url": "",
        "sort_order": 1,
        "is_active": True,
        "slides": [
            {
                "id": "s1",
                "image_url": "/slide1.jpg",
                "title": {"en": "Slide 1"},
                "description": {"en": "Desc 1"},
            }
        ],
    }


def _company_roadmap_doc():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "cr1",
        "company_name": "Chronostep",
        "role_title": "Intern",
        "period": "2023",
        "employment_type": "internship",
        "location": "Cebu City",
        "role_title_i18n": {"en": "Intern", "ceb": "Intern", "fil_PH": "Intern"},
        "definition": "Definition",
        "definition_i18n": {"en": "Definition", "ceb": "", "fil_PH": ""},
        "summary": "Summary",
        "summary_i18n": {"en": "Summary", "ceb": "", "fil_PH": ""},
        "highlights": ["One"],
        "highlights_i18n": {"en": ["One"], "ceb": [], "fil_PH": []},
        "cover_image_url": "/roadmap-cover.jpg",
        "activities": [
            {
                "id": "a1",
                "image_url": "/activity.jpg",
                "title": {"en": "Activity"},
                "caption": {"en": "Caption"},
                "sort_order": 0,
            }
        ],
        "accent_color": "#2962ff",
        "sort_order": 1,
        "is_active": True,
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


def _login_attempt_doc():
    return {"_id": "127.0.0.1", "attempts": 0, "lockout_until": None}


def _dummy_like_doc():
    return _DummyModel({"like": True})


def _dummy_model_list(kind: str):
    if kind == "gallery":
        return [_DummyModel(_gallery_doc())]
    if kind == "video":
        return [_DummyModel(_video_doc())]
    if kind == "music":
        return [_DummyModel(_music_doc())]
    if kind == "key_project":
        return [_DummyModel(_key_project_doc())]
    if kind == "company_roadmap":
        return [_DummyModel(_company_roadmap_doc())]
    if kind == "visit":
        return [_DummyModel(_system_info_doc())]
    if kind == "login_attempt":
        return [_DummyModel(_login_attempt_doc())]
    return [_DummyModel({"id": "item-1"})]


def _build_service_mock(name="service"):
    svc = MagicMock(name=name)
    svc.update_profile.return_value = ({"message": "ok"}, 200)
    svc.authenticate_admin.return_value = (None, "Invalid username or password.", False)

    svc.count_visits.return_value = {"visitor_total_count": 1, "bot_total_count": 0}
    svc.delete_page_system_info.return_value = {"status": "success", "message": "ok"}
    svc.add_system_info.return_value = {"status": "success", "message": "ok"}

    svc.get_paginated_system_info.return_value = (_dummy_model_list("visit"), 1)
    svc.get_paginated_login_attempt_list.return_value = (_dummy_model_list("login_attempt"), 1)
    svc.get_paginated_gallery_list.return_value = (_dummy_model_list("gallery"), 1)
    svc.get_paginated_video_list.return_value = (_dummy_model_list("video"), 1)
    svc.get_paginated_music_list.return_value = (_dummy_model_list("music"), 1)
    svc.get_paginated_key_projects.return_value = (_dummy_model_list("key_project"), 1)
    svc.get_paginated_company_roadmaps.return_value = (_dummy_model_list("company_roadmap"), 1)
    svc.search_gallery_paginated.return_value = (_dummy_model_list("gallery"), 1)
    svc.search_video_paginated.return_value = (_dummy_model_list("video"), 1)

    svc.get_active_key_projects.return_value = _dummy_model_list("key_project")
    svc.get_active_company_roadmaps.return_value = _dummy_model_list("company_roadmap")
    svc.seed_default_projects_if_empty.return_value = 0
    svc.seed_default_company_roadmaps_if_empty.return_value = 0

    svc.get_gallery_by_id.return_value = _gallery_doc()
    svc.get_video_by_id.return_value = _video_doc()
    svc.get_music_by_id.return_value = _music_doc()
    svc.get_music_by_url.return_value = _music_doc()
    svc.get_key_project_by_id.return_value = _key_project_doc()
    svc.get_company_roadmap_by_id.return_value = _company_roadmap_doc()
    svc.get_login_attempt_by_id.return_value = _login_attempt_doc()

    svc.get_comments.return_value = ([], 0)
    svc.add_comment.return_value = "comment-1"
    svc.toggle_like.return_value = {"liked": True, "like_count": 1}
    svc.count_comments_by_gallery.return_value = 1
    svc.count_comments_by_vlog.return_value = 1
    svc.count_comments_by_vlog_ids.return_value = {"v1": 1, "v2": 0}

    svc.get_gallery_likes_count_by_id.return_value = 1
    svc.get_gallery_likes_by_id_and_ip.return_value = _dummy_like_doc()
    svc.get_vlog_likes_count_by_id.return_value = 1
    svc.get_vlog_likes_counts_by_ids.return_value = {"v1": 1, "v2": 0}
    svc.get_vlog_liked_states_by_ids_and_ip.return_value = {"v1": True, "v2": False}
    svc.get_vlog_likes_by_id_and_ip.return_value = _dummy_like_doc()

    svc.add_gallery.return_value = "gallery-1"
    svc.update_gallery.return_value = True
    svc.delete_gallery.return_value = True
    svc.add_video.return_value = "video-1"
    svc.update_video.return_value = True
    svc.delete_video.return_value = True
    svc.add_music.return_value = "music-1"
    svc.update_music.return_value = True
    svc.delete_music.return_value = True
    svc.add_key_project.return_value = "project-1"
    svc.update_key_project.return_value = True
    svc.delete_key_project.return_value = True
    svc.add_company_roadmap.return_value = "roadmap-1"
    svc.update_company_roadmap.return_value = True
    svc.delete_company_roadmap.return_value = True

    svc.get_all_tags.return_value = ["tag1", "tag2"]
    return svc


def _patch_module_dependencies(stack: ExitStack, module):
    # Replace services with flexible mocks.
    for attr_name in list(vars(module).keys()):
        if attr_name.endswith("_service"):
            stack.enter_context(patch.object(module, attr_name, _build_service_mock(attr_name)))

    if hasattr(module, "cache"):
        fake_cache = MagicMock()
        fake_cache.get.return_value = None
        fake_cache.set.return_value = None
        stack.enter_context(patch.object(module, "cache", fake_cache))

    if hasattr(module, "get_cache_data"):
        stack.enter_context(patch.object(module, "get_cache_data", lambda *a, **k: (None, "test-cache-key")))
    if hasattr(module, "clear_cache_by_prefix"):
        stack.enter_context(patch.object(module, "clear_cache_by_prefix", lambda *a, **k: None))
    if hasattr(module, "get_random_tags"):
        stack.enter_context(patch.object(module, "get_random_tags", lambda *a, **k: []))
    if hasattr(module, "capture_image"):
        stack.enter_context(patch.object(module, "capture_image", lambda *a, **k: (None, None)))
    if hasattr(module, "gettext"):
        stack.enter_context(patch.object(module, "gettext", lambda key, *a, **k: key))
    if hasattr(module, "get_locale"):
        stack.enter_context(patch.object(module, "get_locale", lambda: "en"))
    if hasattr(module, "verify_hcaptcha"):
        stack.enter_context(patch.object(module, "verify_hcaptcha", lambda *a, **k: (True, {})))
    if hasattr(module, "get_request_ip"):
        stack.enter_context(patch.object(module, "get_request_ip", lambda *a, **k: "127.0.0.1"))
    if hasattr(module, "safe_filename_parts"):
        stack.enter_context(patch.object(module, "safe_filename_parts", lambda *a, **k: ("download", "download")))
    if hasattr(module, "stream_generator"):
        stack.enter_context(patch.object(module, "stream_generator", lambda *a, **k: iter([b"data"])))
    if hasattr(module, "stream_with_context"):
        stack.enter_context(patch.object(module, "stream_with_context", lambda g: g))
    if hasattr(module, "render_template"):
        stack.enter_context(patch.object(module, "render_template", lambda *a, **k: "rendered-template"))
    if hasattr(module, "url_for"):
        stack.enter_context(
            patch.object(module, "url_for", lambda endpoint, *a, **k: f"/{str(endpoint).replace('.', '/')}")
        )
    if hasattr(module, "redirect"):
        stack.enter_context(patch.object(module, "redirect", lambda url, *a, **k: _DummyRedirectResponse(url)))
    if hasattr(module, "flash"):
        stack.enter_context(patch.object(module, "flash", lambda *a, **k: None))
    if hasattr(module, "LoginForm"):
        stack.enter_context(patch.object(module, "LoginForm", _DummyForm))
    if hasattr(module, "admin_login_security"):
        gate = SimpleNamespace(allowed=True, message="", retry_after_seconds=0)
        sec = MagicMock()
        sec.issue_form_challenge.return_value = {
            "admin_login_nonce": "nonce",
            "admin_login_honeypot_field": "company_website",
        }
        sec.validate_form_submission.return_value = gate
        sec.check_before_auth.return_value = gate
        sec.record_failure.return_value = None
        sec.record_success.return_value = None
        stack.enter_context(patch.object(module, "admin_login_security", sec))
    if hasattr(module, "requests"):
        fake_requests = MagicMock()
        fake_requests.get.return_value = _DummyHTTPResponse()
        stack.enter_context(patch.object(module, "requests", fake_requests))


def _iter_controller_functions(module):
    for name, fn in inspect.getmembers(module, inspect.isfunction):
        if fn.__module__ != module.__name__:
            continue
        if name.startswith("_"):
            continue
        yield name, fn


def _dummy_arg_for_param(param_name: str):
    if param_name.endswith("_id") or param_name == "id":
        return "item-1"
    if param_name == "lang_code":
        return "en"
    return "value"


def _request_context_kwargs(module_path: str, function_name: str):
    query = {
        "page": "1",
        "per_page": "10",
        "order": "desc",
        "gallery_id": "g1",
        "vlog_id": "v1",
        "gallery_ids": "g1,g2",
        "vlog_ids": "v1,v2",
        "search": "test",
        "tags": "tag1",
        "url": "https://example.com/audio.mp3",
    }
    headers = {
        "X-Forwarded-For": "127.0.0.1",
        "User-Agent": "Mozilla/5.0",
        "Range": "bytes=0-1023",
        "Referer": "http://localhost/profile?search=old",
    }
    base_kwargs = {
        "path": "/",
        "query_string": query,
        "headers": headers,
        "environ_overrides": {"REMOTE_ADDR": "127.0.0.1"},
    }

    json_routes = {
        "app.Controllers.api.BaseController.delete_page_system_info_route",
        "app.Controllers.api.AuthController.update_profile_route",
        "app.Controllers.api.GalleryCommentController.gallery_like_comment_route",
        "app.Controllers.api.VlogCommentController.vlog_like_comment_route",
    }
    form_post_routes = {
        "app.Controllers.api.GalleryLikeController.add_gallery_like_route",
        "app.Controllers.api.VlogLikeController.add_vlog_like_route",
        "app.Controllers.api.GalleryController.add_gallery_route",
        "app.Controllers.api.GalleryController.update_gallery_route",
        "app.Controllers.api.VideoController.add_video_route",
        "app.Controllers.api.VideoController.update_video_route",
        "app.Controllers.api.MusicController.add_music_route",
        "app.Controllers.api.MusicController.update_music_route",
        "app.Controllers.api.KeyProjectController.add_key_project_route",
        "app.Controllers.api.KeyProjectController.update_key_project_route",
        "app.Controllers.api.CompanyRoadmapController.add_company_roadmap_route",
        "app.Controllers.api.CompanyRoadmapController.update_company_roadmap_route",
    }

    route_key = f"{module_path}.{function_name}"
    if ".Controllers.web." in module_path:
        base_kwargs["method"] = "GET"
        return base_kwargs

    if route_key in json_routes:
        base_kwargs["method"] = "POST"
        base_kwargs["json"] = {
            "records": [{"_id": VALID_OBJECT_ID, "image_capture": None}],
            "comment_id": "comment-1",
            "gallery_id": "g1",
            "vlog_id": "v1",
            "text": "hello",
            "username": "admin",
            "password": "secret",
        }
        return base_kwargs

    if route_key in form_post_routes:
        base_kwargs["method"] = "POST"
        base_kwargs["data"] = {
            "title": '{"en":"Title"}',
            "description": '{"en":"Description"}',
            "gallery_id": '"g1"',
            "vlog_id": '"v1"',
            "artist": "Artist",
            "lyrics": "Lyrics",
            "tags": '["tag1"]',
            "stack": "Python",
            "status": "planned",
            "demo_url": "",
            "repo_url": "",
            "sort_order": "1",
            "is_active": "true",
            "slides_meta": "[]",
            "activities_meta": "[]",
            "company_name": "Company",
            "role_title": "Role",
            "period": "2024",
            "employment_type": "internship",
            "location": "Cebu",
            "definition": "Definition",
            "summary": "Summary",
            "highlights": "One\nTwo",
            "accent_color": "#2962ff",
            "text": "hello",
            "h-captcha-response": "token",
        }
        return base_kwargs

    base_kwargs["method"] = "GET"
    return base_kwargs


def run_controller_module_smoke_test(testcase, module_path: str, min_public_functions: int = 1):
    with patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client):
        module = importlib.import_module(module_path)

    functions = [name for name, _ in _iter_controller_functions(module)]

    testcase.assertGreaterEqual(
        len(functions),
        min_public_functions,
        f"{module_path} exposes {len(functions)} public functions; expected at least {min_public_functions}",
    )


def run_controller_module_functions_test(testcase, module_path: str):
    app = Flask(__name__)
    app.secret_key = "test-secret"

    failures = []
    executed = []

    with ExitStack() as stack:
        stack.enter_context(patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client))
        module = importlib.import_module(module_path)
        _patch_module_dependencies(stack, module)

        for function_name, fn in _iter_controller_functions(module):
            sig = inspect.signature(fn)
            args = []
            for param_name, param in sig.parameters.items():
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue
                if param.default is not inspect._empty:
                    continue
                args.append(_dummy_arg_for_param(param_name))

            try:
                ctx_kwargs = _request_context_kwargs(module_path, function_name)
                path = ctx_kwargs.pop("path", "/")
                with app.test_request_context(path, **ctx_kwargs):
                    # Provide default session state for admin/web controllers.
                    from flask import session
                    session.setdefault("user_id", "user-1")
                    session.setdefault("role", "admin")
                    # For admin_login_route specifically, don't force redirect branch.
                    if function_name == "admin_login_route":
                        session.clear()
                    result = getattr(module, function_name)(*args)
                    # Touch tuple/Response values without asserting response internals.
                    if isinstance(result, tuple):
                        _ = result[0]
                    elif isinstance(result, Response):
                        _ = result.status_code
                executed.append(function_name)
            except Exception as exc:
                failures.append(f"{module_path}.{function_name}: {exc}")

    if failures:
        testcase.fail("Controller function execution failures:\n" + "\n".join(failures))
    testcase.assertGreater(len(executed), 0, f"No controller functions executed for {module_path}")
