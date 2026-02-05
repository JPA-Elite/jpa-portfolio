from backend.Repositories.VisitRepository import VisitRepository
from backend.configurations import SortOrder


class _FakeCollection:
    def __init__(self):
        self._queries = []

    def find(self):
        return [
            {"_id": 1, "timestamp": "01/02/2025 - 12:00 PM"},
            {"_id": 2, "timestamp": "01/01/2025 - 12:00 PM"},
            {"_id": 3, "timestamp": "invalid"},
        ]

    def count_documents(self, query):
        self._queries.append(query)
        if "os" in query and "$not" in query["os"]:
            return 11
        return 4



def test_get_paginated_documents_sorts_and_skips_invalid_timestamp():
    repo = VisitRepository.__new__(VisitRepository)
    repo.collection = _FakeCollection()

    docs, total = repo.get_paginated_documents(page=1, per_page=10, order=SortOrder.DESC)

    assert total == 3
    assert [doc["_id"] for doc in docs] == [1, 2]



def test_count_visits_builds_expected_filters():
    repo = VisitRepository.__new__(VisitRepository)
    fake_collection = _FakeCollection()
    repo.collection = fake_collection

    counts = repo.count_visits({"page": "/profile"})

    assert counts == {"visitor_total_count": 11, "bot_total_count": 4}
    assert fake_collection._queries[0] == {
        "page": "/profile",
        "os": {"$not": {"$regex": "^other$", "$options": "i"}},
    }
    assert fake_collection._queries[1] == {
        "page": "/profile",
        "os": {"$regex": "^other$", "$options": "i"},
    }
