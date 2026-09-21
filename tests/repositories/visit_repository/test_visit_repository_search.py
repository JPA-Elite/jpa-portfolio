import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta
from unittest.mock import patch

from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.VisitRepository import VisitRepository
from app.configurations import SortOrder


class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, *args, **kwargs):
        return self

    def skip(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def __iter__(self):
        return iter(self._docs)


class _FakeCollection:
    def __init__(self, docs):
        self._docs = list(docs)

    def find(self, *args, **kwargs):
        return _FakeCursor([dict(doc) for doc in self._docs])


def _visit_doc(page, timestamp, browser="Chrome", system="Windows"):
    return {
        "system": system,
        "device": "Phone",
        "brand": "Brand",
        "browser": browser,
        "os": "Android",
        "page": page,
        "timestamp": timestamp,
        "ip_address": "127.0.0.1",
        "city": "Cebu",
        "region": "Central Visayas",
        "country": "PH",
        "location": "10,20",
    }


class VisitRepositorySearchTests(unittest.TestCase):
    def _repository_with(self, docs):
        stack = ExitStack()
        stack.enter_context(
            patch.object(
                BaseRepository,
                "get_mongo_client",
                new=lambda self, name: (object(), {}, _FakeCollection(docs)),
            )
        )
        self.addCleanup(stack.close)
        return VisitRepository()

    def test_search_filters_by_page_and_returns_matching_total(self):
        repo = self._repository_with([
            _visit_doc("/music", "09/20/2026 - 10:00 AM"),
            _visit_doc("/portfolio", "09/20/2026 - 11:00 AM"),
            _visit_doc("/gallery", "09/20/2026 - 12:00 PM"),
        ])

        documents, total = repo.get_paginated_documents(1, 10, SortOrder.DESC, "/portfolio")

        self.assertEqual(total, 1)
        self.assertEqual([doc["page"] for doc in documents], ["/portfolio"])

    def test_search_matches_browser_and_is_case_insensitive(self):
        repo = self._repository_with([
            _visit_doc("/music", "09/20/2026 - 10:00 AM", browser="Firefox"),
            _visit_doc("/vlog", "09/20/2026 - 11:00 AM", browser="Chrome"),
        ])

        documents, total = repo.get_paginated_documents(1, 10, SortOrder.DESC, "FIREFOX")

        self.assertEqual(total, 1)
        self.assertEqual(documents[0]["page"], "/music")

    def test_pagination_slices_sorted_documents_and_reports_full_total(self):
        base = datetime(2026, 9, 20, 1, 0)
        docs = [
            _visit_doc(
                f"/page-{index}",
                (base + timedelta(hours=index)).strftime("%m/%d/%Y - %I:%M %p"),
            )
            for index in range(25)
        ]
        repo = self._repository_with(docs)

        first_page, total = repo.get_paginated_documents(1, 10, SortOrder.DESC, "")
        third_page, _ = repo.get_paginated_documents(3, 10, SortOrder.DESC, "")

        self.assertEqual(total, 25)
        self.assertEqual(len(first_page), 10)
        self.assertEqual(len(third_page), 5)
        self.assertEqual(first_page[0]["page"], "/page-24")
        self.assertEqual(first_page[9]["page"], "/page-15")

    def test_records_with_unparsable_timestamps_are_excluded_from_total(self):
        repo = self._repository_with([
            _visit_doc("/music", "09/20/2026 - 10:00 AM"),
            _visit_doc("/gallery", "not-a-timestamp"),
        ])

        documents, total = repo.get_paginated_documents(1, 10, SortOrder.DESC, "")

        self.assertEqual(total, 1)
        self.assertEqual(documents[0]["page"], "/music")


if __name__ == "__main__":
    unittest.main()
