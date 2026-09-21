import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId

from app.Repositories.BaseRepository import BaseRepository
from app.Services.DashboardService import DashboardService
from app.configurations import SortOrder

from tests.services._service_fixtures import build_test_app


class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, spec):
        field, direction = spec[0]
        self._docs.sort(key=lambda doc: doc.get(field), reverse=(direction == -1))
        return self

    def skip(self, count):
        self._docs = self._docs[count:]
        return self

    def limit(self, count):
        self._docs = self._docs[:count]
        return self

    def __iter__(self):
        return iter(self._docs)


class _FakeActivityCollection:
    def __init__(self, docs):
        self._docs = list(docs)

    def _match(self, query):
        clauses = (query or {}).get("$or")
        if not clauses:
            return list(self._docs)

        matched = []
        for doc in self._docs:
            if any(
                str(condition.get("$regex", "")).lower() in str(doc.get(field) or "").lower()
                for clause in clauses
                for field, condition in clause.items()
            ):
                matched.append(doc)
        return matched

    def count_documents(self, query):
        return len(self._match(query))

    def find(self, query, projection=None):
        return _FakeCursor([dict(doc) for doc in self._match(query)])


def _activity_doc(index, method="POST", path="/admin/api/test"):
    return {
        "_id": ObjectId(f"{index:024x}"),
        "timestamp": f"2026-09-20T{index % 24:02d}:00:00Z",
        "method": method,
        "path": path,
        "status_code": 200,
        "remote_addr": "127.0.0.1",
        "user_id": f"user-{index}",
    }


class DashboardServiceRecentActivityTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        stack.enter_context(
            patch.object(
                BaseRepository,
                "get_mongo_client",
                new=lambda self, name: (object(), {}, SimpleNamespace(name=name)),
            )
        )
        self.addCleanup(stack.close)
        self.service = DashboardService()

    def _use_activity_docs(self, docs):
        self.service.activity_repo = SimpleNamespace(collection=_FakeActivityCollection(docs))

    def test_paginates_and_reports_full_total(self):
        docs = [_activity_doc(index) for index in range(1, 26)]
        self._use_activity_docs(docs)

        items, total = self.service.get_paginated_recent_activity(1, 10, SortOrder.DESC, "")

        self.assertEqual(total, 25)
        self.assertEqual(len(items), 10)
        self.assertEqual(items[0]["_id"], str(docs[-1]["_id"]))

    def test_second_page_skips_first_page_records(self):
        docs = [_activity_doc(index) for index in range(1, 26)]
        self._use_activity_docs(docs)

        first_page, _ = self.service.get_paginated_recent_activity(1, 10, SortOrder.DESC, "")
        second_page, _ = self.service.get_paginated_recent_activity(2, 10, SortOrder.DESC, "")

        self.assertEqual(first_page[0]["_id"], str(docs[-1]["_id"]))
        self.assertEqual(second_page[0]["_id"], str(docs[-11]["_id"]))
        self.assertEqual(len(second_page), 10)

    def test_search_filters_and_lowers_total(self):
        docs = [
            _activity_doc(1, path="/admin/api/delete-visits/abc"),
            _activity_doc(2, path="/admin/api/music"),
            _activity_doc(3, path="/admin/api/gallery"),
        ]
        self._use_activity_docs(docs)

        items, total = self.service.get_paginated_recent_activity(1, 10, SortOrder.DESC, "music")

        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["path"], "/admin/api/music")

    def test_returns_empty_page_when_collection_fails(self):
        self.service.activity_repo = SimpleNamespace(collection=SimpleNamespace())

        with build_test_app().app_context():
            items, total = self.service.get_paginated_recent_activity(1, 10, SortOrder.DESC, "")

        self.assertEqual(items, [])
        self.assertEqual(total, 0)


if __name__ == "__main__":
    unittest.main()
