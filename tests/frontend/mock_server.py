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
os.environ["FLASK_DEBUG"] = "0"
os.environ["MONGO_URI"] = "mongodb://127.0.0.1:1/playwright_mock"
os.environ["MONGO_DB"] = "playwright_mock"
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY") or "playwright-mock-secret"

from app.app import app
import app.app as app_module
from app.Controllers.web import PageController
from app.Models.BuiltApp import BuiltApp
from app.Models.CompanyRoadmap import CompanyRoadmap
from app.Models.KeyProject import KeyProject


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


PageController.key_project_service = KeyProjectMockService()
PageController.company_roadmap_service = CompanyRoadmapMockService()
PageController.built_app_service = BuiltAppMockService()
app_module.TRACKED_VISIT_ENDPOINTS = frozenset()
app.config["SESSION_COOKIE_SECURE"] = False


if __name__ == "__main__":
    port = int(os.environ.get("PLAYWRIGHT_MOCK_PORT", "4173"))
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)
