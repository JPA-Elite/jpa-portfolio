from dataclasses import dataclass
from types import SimpleNamespace

from bson import ObjectId

from app.configurations import SortOrder


VALID_OBJECT_ID = "507f1f77bcf86cd799439011"


class DummyModel:
    def __init__(self, data=None, **kwargs):
        self._data = dict(data or {})
        self._data.update(kwargs)
        self._id = self._data.get("_id", VALID_OBJECT_ID)

        for key, value in self._data.items():
            setattr(self, key, value)

    def __getitem__(self, key):
        return self.to_dict()[key]

    def __getattr__(self, item):
        data = self.to_dict()
        if item in data:
            return data[item]
        raise AttributeError(item)

    def to_dict(self):
        data = {
            "_id": self._data.get("_id", VALID_OBJECT_ID),
            "id": self._data.get("id", "item-1"),
            "title": self._data.get("title", {"en": "Title"}),
            "description": self._data.get("description", {"en": "Description"}),
            "image_url": self._data.get("image_url", "/img.png"),
            "video_url": self._data.get("video_url", "/video.mp4"),
            "url": self._data.get("url", "/audio.mp3"),
            "image": self._data.get("image", "/cover.jpg"),
            "duration": self._data.get("duration", "1:23"),
            "artist": self._data.get("artist", "Artist"),
            "tags": self._data.get("tags", ["tag"]),
            "gallery_id": self._data.get("gallery_id", "g1"),
            "vlog_id": self._data.get("vlog_id", "v1"),
            "ip_address": self._data.get("ip_address", "127.0.0.1"),
            "like": self._data.get("like", True),
            "liked_ips": self._data.get("liked_ips", []),
            "author_name": self._data.get("author_name", "user_127001"),
            "text": self._data.get("text", "hello"),
            "attempts": self._data.get("attempts", 0),
            "lockout_until": self._data.get("lockout_until"),
            "company_name": self._data.get("company_name", "Company"),
            "role_title": self._data.get("role_title", "Role"),
            "period": self._data.get("period", "2024"),
            "employment_type": self._data.get("employment_type", "Internship"),
            "location": self._data.get("location", "Cebu City"),
            "definition": self._data.get("definition", "Definition"),
            "summary": self._data.get("summary", "Summary"),
            "highlights": self._data.get("highlights", ["Highlight"]),
            "activities": self._data.get("activities", []),
            "accent_color": self._data.get("accent_color", "#2962ff"),
            "sort_order": self._data.get("sort_order", 0),
            "is_active": self._data.get("is_active", True),
            "slides": self._data.get("slides", []),
            "status": self._data.get("status", "planned"),
            "demo_url": self._data.get("demo_url", ""),
            "repo_url": self._data.get("repo_url", ""),
            "file": self._data.get("file", None),
        }
        return data


class FakeCursor:
    def __init__(self, items=None):
        self.items = list(items or [])

    def sort(self, *args, **kwargs):
        return self

    def skip(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def __iter__(self):
        return iter(self.items)


class FakeCollection:
    def __init__(self):
        self._docs = [
            {
                "_id": VALID_OBJECT_ID,
                "id": "item-1",
                "title": {"en": "Title"},
                "description": {"en": "Description"},
                "image_url": "/image.jpg",
                "video_url": "/video.mp4",
                "url": "/audio.mp3",
                "image": "/cover.jpg",
                "duration": "1:00",
                "artist": "Artist",
                "tags": ["tag1"],
                "gallery_id": "g1",
                "vlog_id": "v1",
                "ip_address": "127.0.0.1",
                "like": True,
                "liked_ips": ["127.0.0.1"],
                "author_name": "user_127001",
                "text": "hello",
                "attempts": 0,
                "lockout_until": None,
                "role_title": "Role",
                "company_name": "Company",
                "period": "2024",
                "employment_type": "Internship",
                "location": "Cebu City",
                "definition": "Definition",
                "summary": "Summary",
                "highlights": ["One"],
                "activities": [],
                "accent_color": "#2962ff",
                "sort_order": 0,
                "is_active": True,
                "slides": [],
                "status": "planned",
                "timestamp": "01/01/2026 - 12:00 PM",
                "os": "Windows",
            }
        ]

    def find_one(self, *args, **kwargs):
        return dict(self._docs[0])

    def find(self, *args, **kwargs):
        return FakeCursor([dict(self._docs[0])])

    def aggregate(self, *args, **kwargs):
        return [dict(self._docs[0])]

    def count_documents(self, *args, **kwargs):
        return 1

    def insert_one(self, *args, **kwargs):
        return SimpleNamespace(inserted_id=VALID_OBJECT_ID)

    def insert_many(self, *args, **kwargs):
        return SimpleNamespace(inserted_ids=[VALID_OBJECT_ID])

    def update_one(self, *args, **kwargs):
        return SimpleNamespace(matched_count=1, modified_count=1, upserted_id=None)

    def delete_one(self, *args, **kwargs):
        return SimpleNamespace(deleted_count=1)

    def delete_many(self, *args, **kwargs):
        return SimpleNamespace(deleted_count=2)

    def distinct(self, *args, **kwargs):
        return ["tag1", "tag2"]


@dataclass
class DummyFile:
    filename: str = "file.dat"
    content_type: str = "image/png"

    def save(self, path):
        with open(path, "wb") as fp:
            fp.write(b"dummy")


def dummy_repo_model():
    return DummyModel()


def dummy_repo_param(name):
    name = str(name)
    if name == "order":
        return SortOrder.ASC
    if name in {"page"}:
        return 1
    if name in {"per_page", "limit"}:
        return 5
    if name in {"search_query"}:
        return "test"
    if name in {"tags"}:
        return ["tag1"]
    if name in {"roadmaps", "key_projects", "built_apps"}:
        return [dummy_repo_model(), dummy_repo_model()]
    if name in {"locale"}:
        return "en"
    if name in {"fields"}:
        return {"_id": 1}
    if name in {"where_condition"}:
        return {}
    if name in {"success"}:
        return False
    if name in {"ip_address"}:
        return "127.0.0.1"
    if name.endswith("_ids"):
        return ["item-1", "item-2"]
    if name.endswith("_id") or name == "id":
        return VALID_OBJECT_ID
    if name == "object_id":
        return ObjectId(VALID_OBJECT_ID)
    if name in {
        "gallery", "video", "music", "key_project", "roadmap",
        "gallery_like", "vlog_like", "comment", "vlog", "portfolio_data", "system_info"
    }:
        return dummy_repo_model()
    if name == "built_app":
        from app.Models.BuiltApp import BuiltApp
        return BuiltApp.from_dict({
            "id": "app-1",
            "slug": "taskflow",
            "platform": "Mobile",
            "version": "v1.0.0",
            "icon": "apps-outline",
            "name": {"en": "TaskFlow"},
            "short_description": {"en": "Task manager."},
            "full_description": {"en": ["Paragraph."]},
            "snapshots": [],
            "download_url": "#",
            "sort_order": 1,
            "is_active": True,
        })
    return "value"
