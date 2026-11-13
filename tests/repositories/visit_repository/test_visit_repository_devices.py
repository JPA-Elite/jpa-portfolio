import unittest
from contextlib import ExitStack
from unittest.mock import patch

from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.VisitRepository import VisitRepository


class _FakeCollection:
    def __init__(self, entries=None, fail=False):
        self._entries = list(entries or [])
        self._fail = fail

    def aggregate(self, *args, **kwargs):
        if self._fail:
            raise RuntimeError("aggregation failed")
        return list(self._entries)


class VisitRepositoryDeviceBreakdownTests(unittest.TestCase):
    def _repository_with(self, entries=None, fail=False):
        stack = ExitStack()
        stack.enter_context(
            patch.object(
                BaseRepository,
                "get_mongo_client",
                new=lambda self, name: (object(), {}, _FakeCollection(entries, fail)),
            )
        )
        self.addCleanup(stack.close)
        return VisitRepository()

    def test_normalizes_platform_labels_and_sorts_by_count(self):
        repo = self._repository_with([
            {"_id": "iPhone", "count": 25},
            {"_id": "iOS", "count": 5},
            {"_id": "Windows", "count": 40},
            {"_id": "Android", "count": 10},
        ])

        breakdown = repo.get_device_breakdown()

        self.assertEqual(
            breakdown,
            [
                {"label": "Windows", "count": 40},
                {"label": "iOS", "count": 30},
                {"label": "Android", "count": 10},
            ],
        )

    def test_buckets_remaining_platforms_into_other(self):
        repo = self._repository_with([
            {"_id": "Windows", "count": 50},
            {"_id": "iOS", "count": 30},
            {"_id": "Android", "count": 20},
            {"_id": "macOS", "count": 10},
            {"_id": "Linux", "count": 5},
            {"_id": "ChromeOS", "count": 4},
        ])

        breakdown = repo.get_device_breakdown(max_slices=4)

        self.assertEqual(len(breakdown), 4)
        self.assertEqual(breakdown[-1], {"label": "Other", "count": 19})

    def test_returns_empty_list_when_aggregation_fails(self):
        repo = self._repository_with(fail=True)

        self.assertEqual(repo.get_device_breakdown(), [])


if __name__ == "__main__":
    unittest.main()