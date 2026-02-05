from bson import ObjectId

from backend.Services import VisitService as visit_service_module
from backend.Services.VisitService import VisitService


class _FakeVisitRepository:
    def __init__(self):
        self.deleted_ids = []

    def get_paginated_documents(self, page, per_page, order):
        return [
            {
                "system": "x",
                "node": "n",
                "release": "r",
                "version": "v",
                "platform": "p",
                "architecture": "a",
                "user_agent": "ua",
                "device": "d",
                "brand": "b",
                "model": "m",
                "browser": "br",
                "browser_version": "1",
                "os": "linux",
                "os_version": "1",
                "page": "/",
                "timestamp": "now",
            }
        ], 1

    def delete_system_info_by_id(self, object_id):
        self.deleted_ids.append(object_id)

    def count_visits(self, where_condition=None):
        return {"visitor_total_count": 2, "bot_total_count": 1}



def test_get_paginated_system_info_maps_to_models():
    service = VisitService(repository=_FakeVisitRepository())

    docs, total = service.get_paginated_system_info(page=1, per_page=10)

    assert total == 1
    assert len(docs) == 1
    assert docs[0].to_dict()["os"] == "linux"



def test_delete_page_system_info_deletes_db_records_and_cloudinary(monkeypatch):
    repo = _FakeVisitRepository()
    service = VisitService(repository=repo)
    deleted_urls = []

    monkeypatch.setattr(
        visit_service_module,
        "delete_image_from_cloudinary",
        lambda url: deleted_urls.append(url),
    )

    object_id = str(ObjectId())
    result = service.delete_page_system_info(
        [
            {"_id": object_id, "image_capture": "https://cloudinary.example/img1"},
            {"_id": str(ObjectId()), "image_capture": None},
        ]
    )

    assert result["status"] == "success"
    assert len(repo.deleted_ids) == 2
    assert deleted_urls == ["https://cloudinary.example/img1"]



def test_count_visits_delegates_to_repository():
    service = VisitService(repository=_FakeVisitRepository())

    assert service.count_visits({"page": "/"}) == {
        "visitor_total_count": 2,
        "bot_total_count": 1,
    }
