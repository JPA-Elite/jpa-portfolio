from datetime import datetime

from flask import Flask

from tests.test_support import VALID_OBJECT_ID


def build_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret"
    return app


def gallery_doc():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "g1",
        "title": {"en": "Gallery"},
        "description": {"en": "Description"},
        "image_url": "/img.jpg",
        "tags": ["tag1"],
    }


def video_doc():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "v1",
        "title": {"en": "Video"},
        "description": {"en": "Description"},
        "file": None,
        "video_url": "/video.mp4",
        "tags": ["tag1"],
    }


def music_doc():
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


def key_project_doc():
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
        "slides": [],
    }


def built_app_doc():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "app1",
        "slug": "taskflow",
        "platform": "Mobile",
        "version": "v1.2.0",
        "icon": "checkmark-done-outline",
        "icon_image_url": "",
        "name": {"en": "TaskFlow"},
        "short_description": {"en": "Task manager."},
        "full_description": {"en": ["Paragraph one.", "Paragraph two."]},
        "snapshots": [],
        "download_url": "#",
        "sort_order": 1,
        "is_active": True,
    }


def roadmap_doc():
    return {
        "_id": VALID_OBJECT_ID,
        "id": "cr1",
        "company_name": "Chronostep",
        "role_title": "Intern",
        "period": "2023",
        "employment_type": "Internship",
        "location": "Cebu City",
        "role_title_i18n": {"en": "Intern", "ceb": "Intern", "fil_PH": "Intern"},
        "definition": "Definition",
        "definition_i18n": {"en": "Definition", "ceb": "", "fil_PH": ""},
        "summary": "Summary",
        "summary_i18n": {"en": "Summary", "ceb": "", "fil_PH": ""},
        "highlights": ["One"],
        "highlights_i18n": {"en": ["One"], "ceb": [], "fil_PH": []},
        "cover_image_url": "/cover.jpg",
        "activities": [],
        "accent_color": "#2962ff",
        "sort_order": 1,
        "is_active": True,
    }


def comment_doc(item_key="gallery_id"):
    return {
        "_id": VALID_OBJECT_ID,
        item_key: "item-1",
        "author_name": "user_127001",
        "text": "hello",
        "ip_address": "127.0.0.1",
        "liked_ips": ["127.0.0.1"],
        "created_at": datetime.now(),
    }


def system_info_doc():
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
