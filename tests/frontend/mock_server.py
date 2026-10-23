import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

os.environ["DDOS_GUARD_ENABLED"] = "false"
os.environ["DOMAIN_ROUTING_ENABLED"] = "false"
os.environ["LANDING_DOMAIN"] = "jpastack.local"
os.environ["PROFESSIONAL_DOMAIN"] = "professional.jpastack.local"
os.environ["SOCIAL_DOMAIN"] = "jpastack.local"
os.environ["ADMIN_DOMAIN"] = "admin.jpastack.local"
os.environ["HCAPTCHA_ENABLED"] = "false"
os.environ["ADMIN_LOGIN_GUARD_ENABLED"] = "false"
os.environ["FLASK_DEBUG"] = "0"
os.environ["MONGO_URI"] = "mongodb://127.0.0.1:1/playwright_mock"
os.environ["MONGO_DB"] = "playwright_mock"
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY") or "playwright-mock-secret"

from flask import jsonify, request, session
from app.app import app
import app.app as app_module
from app.constants.login_roles import ROLE_ADMIN
from app.Controllers.web import AdminPageController, PageController
from app.Controllers.api import AdminOtpController
from app.Models.BuiltApp import BuiltApp
from app.Models.CompanyRoadmap import CompanyRoadmap
from app.Models.Gallery import Gallery
from app.Models.KeyProject import KeyProject
from app.Models.Video import Video


def mock_image(name):
    return f"/static/images/{name}"


KEY_PROJECTS = [
    KeyProject(
        id="pw-key-project-alpha",
        title={"en": "Mock Project Alpha"},
        description={
            "en": "A deterministic project rendered from the live portfolio template."
        },
        stack={"en": "Python • Flask • MongoDB"},
        status="shipped",
        image_url=mock_image("jaom.webp"),
        demo_url="https://example.com/mock-project-alpha/demo",
        repo_url="https://example.com/mock-project-alpha/repo",
        sort_order=1,
        slides=[
            {
                "title": {"en": "Mock Project Alpha Preview"},
                "description": {"en": "Second project preview image."},
                "image_url": mock_image("jaom_home.webp"),
            }
        ],
    ),
    KeyProject(
        id="pw-key-project-beta",
        title={"en": "Mock Project Beta"},
        description={
            "en": "A preview-only project used to validate the project modal."
        },
        stack={"en": "JavaScript • Vite"},
        status="shipped",
        image_url=mock_image("jaom_about_us.webp"),
        sort_order=2,
        slides=[
            {
                "title": {"en": "Mock Project Beta Preview"},
                "description": {"en": "Second project preview image."},
                "image_url": mock_image("Capture.webp"),
            }
        ],
    ),
]

COMPANY_ROADMAPS = [
    CompanyRoadmap(
        id="pw-company-roadmap",
        company_name="Mock Company",
        role_title="Mock Software Engineer",
        period="2024 - Present",
        employment_type="full-time",
        location="Remote",
        definition="A deterministic role rendered from the live roadmap template.",
        summary="Builds mocked pages for frontend regression coverage.",
        highlights=[
            "Rendered the current portfolio template with fixed mock data.",
            "Covered desktop and mobile responsive layouts.",
        ],
        cover_image_url=mock_image("jaom.webp"),
        activities=[
            {
                "image_url": mock_image("jaom_home.webp"),
                "title": {"en": "Mock Activity One"},
                "caption": {"en": "First deterministic snapshot."},
            },
            {
                "image_url": mock_image("jaom_about_us.webp"),
                "title": {"en": "Mock Activity Two"},
                "caption": {"en": "Second deterministic snapshot."},
            },
        ],
        accent_color="#2962ff",
        sort_order=1,
    ),
]

BUILT_APPS = [
    BuiltApp(
        id="pw-built-app-main",
        slug="mock-app",
        platform="Mobile",
        version="1.0.0",
        icon="apps-outline",
        icon_image_url=mock_image("cert1.webp"),
        name={"en": "Mock App"},
        short_description={
            "en": "A deterministic app rendered from the live built-app template."
        },
        full_description={
            "en": [
                "This app is rendered from the current Flask and Jinja templates.",
                "All content comes from fixed in-memory mock data.",
            ]
        },
        snapshots=[
            {
                "id": "mock-snapshot-1",
                "image_url": mock_image("cert1.webp"),
                "sort_order": 0,
            },
            {
                "id": "mock-snapshot-2",
                "image_url": mock_image("cert2.webp"),
                "sort_order": 1,
            },
            {
                "id": "mock-snapshot-3",
                "image_url": mock_image("cert3.webp"),
                "sort_order": 2,
            },
            {
                "id": "mock-snapshot-4",
                "image_url": mock_image("cert4.webp"),
                "sort_order": 3,
            },
        ],
        technologies=[
            {"key": "language", "value": "Python"},
            {"key": "framework", "value": "Flask"},
            {"key": "database", "value": "MongoDB"},
            {"key": "storage", "value": "Cloudinary"},
            {"key": "tooling", "value": "Playwright"},
        ],
        download_url="https://example.com/mock-app-download",
        sort_order=1,
    ),
    BuiltApp(
        id="pw-built-app-secondary",
        slug="mock-app-secondary",
        platform="Desktop",
        version="2.0.0",
        icon="desktop-outline",
        icon_image_url=mock_image("cert2.webp"),
        name={"en": "Second Mock App"},
        short_description={
            "en": "A secondary deterministic app for related-app coverage."
        },
        full_description={
            "en": ["This secondary app is also rendered from the live templates."]
        },
        snapshots=[
            {
                "id": "mock-snapshot-secondary",
                "image_url": mock_image("cert5.webp"),
                "sort_order": 0,
            }
        ],
        technologies=[{"key": "language", "value": "JavaScript"}],
        download_url="",
        sort_order=2,
    ),
]


GALLERY_ITEMS = [
    Gallery(
        id="pw-gallery-sunrise",
        title={"en": "Mock Gallery Sunrise"},
        description={
            "en": "A calm sunrise over the deterministic test horizon."
        },
        image_url=mock_image("jaom.webp"),
        tags=["alpha", "sunrise"],
        _id="pw-gallery-sunrise",
    ),
    Gallery(
        id="pw-gallery-forest",
        title={"en": "Mock Gallery Forest"},
        description={
            "en": "A quiet forest with a phosphorescent canopy."
        },
        image_url=mock_image("jaom_home.webp"),
        tags=["beta", "nature"],
        _id="pw-gallery-forest",
    ),
    Gallery(
        id="pw-gallery-city",
        title={"en": "Mock Gallery City"},
        description={
            "en": "A busy city rendered for the gallery pagination check."
        },
        image_url=mock_image("jaom_about_us.webp"),
        tags=["gamma", "urban"],
        _id="pw-gallery-city",
    ),
    Gallery(
        id="pw-gallery-ocean",
        title={"en": "Mock Gallery Ocean"},
        description={
            "en": "An ocean wave used for the tag filter check."
        },
        image_url=mock_image("Capture.webp"),
        tags=["alpha", "water"],
        _id="pw-gallery-ocean",
    ),
    Gallery(
        id="pw-gallery-mountain",
        title={"en": "Mock Gallery Mountain"},
        description={
            "en": "A mountain ridge for deterministic snapshots."
        },
        image_url=mock_image("cert1.webp"),
        tags=["beta", "nature"],
        _id="pw-gallery-mountain",
    ),
    Gallery(
        id="pw-gallery-night",
        title={"en": "Mock Gallery Night"},
        description={
            "en": "A night skyline for the gallery modal coverage."
        },
        image_url=mock_image("cert2.webp"),
        tags=["gamma", "urban"],
        _id="pw-gallery-night",
    ),
    Gallery(
        id="pw-gallery-desert",
        title={"en": "Mock Gallery Desert"},
        description={
            "en": "A desert dune from the mock gallery fixture."
        },
        image_url=mock_image("cert3.webp"),
        tags=["delta", "sand"],
        _id="pw-gallery-desert",
    ),
    Gallery(
        id="pw-gallery-aurora",
        title={"en": "Mock Gallery Aurora"},
        description={
            "en": "An aurora used to verify search matching."
        },
        image_url=mock_image("cert4.webp"),
        tags=["epsilon", "sky"],
        _id="pw-gallery-aurora",
    ),
]

VLOG_ITEMS = [
    Video(
        id="pw-vlog-first",
        title={"en": "Mock Vlog First"},
        description={
            "en": "First deterministic vlog description."
        },
        file=None,
        video_url="https://example.com/mock-vlog-first.mp4",
        tags=["alpha", "studio"],
        _id="pw-vlog-first",
    ),
    Video(
        id="pw-vlog-second",
        title={"en": "Mock Vlog Second"},
        description={
            "en": "Second deterministic vlog description with phosphorescent lighting."
        },
        file=None,
        video_url="https://example.com/mock-vlog-second.mp4",
        tags=["beta", "outside"],
        _id="pw-vlog-second",
    ),
    Video(
        id="pw-vlog-third",
        title={"en": "Mock Vlog Third"},
        description={
            "en": "Third deterministic vlog for pagination coverage."
        },
        file=None,
        video_url="https://example.com/mock-vlog-third.mp4",
        tags=["alpha", "tutorial"],
        _id="pw-vlog-third",
    ),
    Video(
        id="pw-vlog-fourth",
        title={"en": "Mock Vlog Fourth"},
        description={
            "en": "Fourth deterministic vlog for card modals."
        },
        file=None,
        video_url="https://example.com/mock-vlog-fourth.mp4",
        tags=["gamma", "urban"],
        _id="pw-vlog-fourth",
    ),
    Video(
        id="pw-vlog-aurora",
        title={"en": "Mock Vlog Aurora"},
        description={
            "en": "An aurora search target for vlogs."
        },
        file=None,
        video_url="https://example.com/mock-vlog-aurora.mp4",
        tags=["epsilon", "night"],
        _id="pw-vlog-aurora",
    ),
]


def _localized_text(value, locale):
    if isinstance(value, dict):
        return str(value.get(locale) or value.get("en") or "")
    return str(value or "")


def _matches_search(item, search_query, locale):
    if not search_query:
        return True

    needle = search_query.casefold()
    haystack = " ".join(
        [
            _localized_text(item.title, locale),
            _localized_text(item.description, locale),
        ]
    ).casefold()
    return needle in haystack


def _matches_tags(item, tags_query):
    if not tags_query:
        return True

    if isinstance(tags_query, str):
        requested = [tag for tag in tags_query.split(".") if tag]
    else:
        requested = [str(tag) for tag in tags_query if tag]

    if not requested:
        return True

    return any(tag in item.tags for tag in requested)


def _paginate(items, page, per_page):
    start = max(0, (page - 1) * per_page)
    return items[start:start + per_page], len(items)


def _all_tags(items):
    tags = []
    for item in items:
        for tag in item.tags:
            if tag not in tags:
                tags.append(tag)
    return tags


class GalleryMockService:
    def search_gallery_paginated(
        self, search_query, tags, locale, page, per_page, order=None
    ):
        filtered = [
            item
            for item in GALLERY_ITEMS
            if _matches_search(item, search_query, locale)
            and _matches_tags(item, tags)
        ]
        return _paginate(filtered, page, per_page)

    def get_all_tags(self, limit=50):
        return _all_tags(GALLERY_ITEMS)[:limit]


class VideoMockService:
    def search_video_paginated(
        self, search_query, tags, locale, page, per_page, order=None
    ):
        filtered = [
            item
            for item in VLOG_ITEMS
            if _matches_search(item, search_query, locale)
            and _matches_tags(item, tags)
        ]
        return _paginate(filtered, page, per_page)

    def get_all_tags(self, limit=50):
        return _all_tags(VLOG_ITEMS)[:limit]


class KeyProjectMockService:
    def seed_default_projects_if_empty(self):
        return None

    def get_active_key_projects(self):
        return KEY_PROJECTS


class CompanyRoadmapMockService:
    def seed_default_company_roadmaps_if_empty(self):
        return None

    def get_active_company_roadmaps(self):
        return COMPANY_ROADMAPS


class BuiltAppMockService:
    def seed_default_built_apps_if_empty(self):
        return None

    def get_active_built_apps(self):
        return BUILT_APPS

    def get_active_built_app_by_slug(self, slug):
        for built_app in BUILT_APPS:
            if built_app.slug == slug:
                return built_app
        return None


class AdminAuthMockService:
    def authenticate_admin(self, username, password):
        if username == "admin" and password == "admin-pass":
            return (
                {
                    "_id": "pw-admin",
                    "username": "Mock Admin",
                    "role": ROLE_ADMIN,
                    "profile_image": "/static/images/user.webp",
                },
                "Login successful!",
                False,
            )
        return None, "Invalid username or password.", False


class AdminOtpMockService:
    email = "admin@example.com"
    valid_otp = "123456"
    sent_count = 0

    def get_user_email(self, user_id):
        return self.email

    def update_user_email(self, user_id, email):
        type(self).email = email
        return True

    def get_cooldown_remaining_seconds(self, user_id):
        return 0

    def send_otp(self, user_id, email):
        type(self).email = email or self.email
        type(self).sent_count += 1
        return "OTP sent to your email."

    def verify_otp(self, user_id, otp):
        if otp == self.valid_otp:
            return {"ok": True, "message": "OTP verified"}
        return {
            "ok": False,
            "reason": "invalid",
            "message": "Invalid OTP.",
            "attempts_remaining": 4,
            "retry_after_seconds": None,
        }


AdminPageController.auth_service = AdminAuthMockService()
AdminOtpController.OtpService = AdminOtpMockService


@app.route("/__playwright/admin-session", methods=["GET"])
def playwright_admin_session():
    face_verified = request.args.get("face_verified", "1") != "0"
    session.clear()
    session["user_id"] = "pw-admin"
    session["role"] = ROLE_ADMIN
    session["username"] = "Mock Admin"
    session["profile_image"] = "/static/images/user.webp"
    if face_verified:
        session["face_verified"] = True
    return "", 204


@app.route("/__playwright/face-verify", methods=["POST"])
def playwright_face_verify():
    if not session.get("user_id"):
        return jsonify({"ok": False, "message": "Not authenticated"}), 401
    session["face_verified"] = True
    return jsonify({"ok": True, "message": "Face verified successfully."})


PageController.gallery_service = GalleryMockService()
PageController.video_service = VideoMockService()
PageController.key_project_service = KeyProjectMockService()
PageController.company_roadmap_service = CompanyRoadmapMockService()
PageController.built_app_service = BuiltAppMockService()
app_module.TRACKED_VISIT_ENDPOINTS = frozenset()
app.config["SESSION_COOKIE_SECURE"] = False


if __name__ == "__main__":
    port = int(os.environ.get("PLAYWRIGHT_MOCK_PORT", "4173"))
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)
