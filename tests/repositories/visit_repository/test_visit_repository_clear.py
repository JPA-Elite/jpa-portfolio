import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.VisitRepository import VisitRepository


class _ClearCollection:
    def __init__(self, deleted_count=0, error=None):
        self.deleted_count = deleted_count
        self.error = error

    def delete_many(self, filter):
        if self.error:
            raise self.error
        return SimpleNamespace(deleted_count=self.deleted_count)


class VisitRepositoryClearTests(unittest.TestCase):
    def _repository_with(self, collection):
        stack = ExitStack()
        stack.enter_context(
            patch.object(
                BaseRepository,
                "get_mongo_client",
                new=lambda self, name: (object(), {}, collection),
            )
        )
        self.addCleanup(stack.close)
        return VisitRepository()

    def test_delete_all_visitors_returns_success_payload_with_count(self):
        repo = self._repository_with(_ClearCollection(deleted_count=3))

        result = repo.delete_all_visitors()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["deleted_count"], 3)
        self.assertIn("3", result["message"])

    def test_delete_all_visitors_returns_success_when_collection_is_empty(self):
        repo = self._repository_with(_ClearCollection(deleted_count=0))

        result = repo.delete_all_visitors()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["deleted_count"], 0)

    def test_delete_all_visitors_returns_error_payload_when_delete_fails(self):
        repo = self._repository_with(_ClearCollection(error=RuntimeError("boom")))

        result = repo.delete_all_visitors()

        self.assertEqual(result["status"], "error")
        self.assertIn("boom", result["message"])


if __name__ == "__main__":
    unittest.main()
