import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.BookingRequestRepository import BookingRequestRepository
from app.configurations import SortOrder
from tests.test_support import VALID_OBJECT_ID


class _RecordingCursor:
    def __init__(self, docs):
        self.docs = list(docs)
        self.sort_calls = []
        self.skip_calls = []
        self.limit_calls = []

    def sort(self, *args, **kwargs):
        self.sort_calls.append((args, kwargs))
        return self

    def skip(self, *args, **kwargs):
        self.skip_calls.append((args, kwargs))
        return self

    def limit(self, *args, **kwargs):
        self.limit_calls.append((args, kwargs))
        return self

    def __iter__(self):
        return iter(self.docs)


class BookingRequestRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.collection = MagicMock()
        self.patcher = patch.object(
            BaseRepository,
            "get_mongo_client",
            new=lambda repository, collection_name: (
                object(),
                {},
                self.collection,
            ),
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.repo = BookingRequestRepository()

    def test_insert_booking_delegates_to_insert_one(self):
        self.collection.insert_one.return_value = SimpleNamespace(
            inserted_id=VALID_OBJECT_ID
        )
        booking = {"name": "Joshua", "email": "joshua@example.com"}

        result = self.repo.insert_booking(booking)

        self.assertEqual(result.inserted_id, VALID_OBJECT_ID)
        self.collection.insert_one.assert_called_once_with(booking)

    def test_find_by_id_uses_object_id_for_valid_id(self):
        self.collection.find_one.return_value = {"_id": ObjectId(VALID_OBJECT_ID)}

        result = self.repo.find_by_id(VALID_OBJECT_ID)

        self.assertEqual(result["_id"], ObjectId(VALID_OBJECT_ID))
        self.collection.find_one.assert_called_once_with(
            {"_id": ObjectId(VALID_OBJECT_ID)}, None
        )

    def test_find_by_id_uses_string_when_id_is_invalid(self):
        self.collection.find_one.return_value = {"_id": "booking-1"}

        result = self.repo.find_by_id("booking-1")

        self.assertEqual(result["_id"], "booking-1")
        self.collection.find_one.assert_called_once_with({"_id": "booking-1"}, None)

    def test_get_paginated_list_with_search_returns_docs_and_total(self):
        cursor = _RecordingCursor([{"_id": VALID_OBJECT_ID}])
        self.collection.find.return_value = cursor
        self.collection.count_documents.return_value = 7

        docs, total = self.repo.get_paginated_list(
            page=3, per_page=2, order=SortOrder.DESC, search_query="josh.ua"
        )

        self.assertEqual(docs, [{"_id": VALID_OBJECT_ID}])
        self.assertEqual(total, 7)
        query = self.collection.find.call_args.args[0]
        self.assertEqual(
            query,
            {
                "$or": [
                    {"name": {"$regex": "josh\\.ua", "$options": "i"}},
                    {"email": {"$regex": "josh\\.ua", "$options": "i"}},
                ]
            },
        )
        self.assertEqual(cursor.sort_calls[0][0], ([("created_at", -1)],))
        self.assertEqual(cursor.skip_calls[0][0], (4,))
        self.assertEqual(cursor.limit_calls[0][0], (2,))
        self.collection.count_documents.assert_called_once_with(query)

    def test_get_paginated_list_without_search_uses_ascending_sort(self):
        cursor = _RecordingCursor([])
        self.collection.find.return_value = cursor
        self.collection.count_documents.return_value = 0

        docs, total = self.repo.get_paginated_list(
            page=1, per_page=5, order=SortOrder.ASC
        )

        self.assertEqual(docs, [])
        self.assertEqual(total, 0)
        self.collection.find.assert_called_once_with({}, None)
        self.assertEqual(cursor.sort_calls[0][0], ([("created_at", 1)],))
        self.assertEqual(cursor.skip_calls, [])
        self.assertEqual(cursor.limit_calls[0][0], (5,))

    def test_get_paginated_list_strips_search_whitespace(self):
        cursor = _RecordingCursor([])
        self.collection.find.return_value = cursor
        self.collection.count_documents.return_value = 0

        self.repo.get_paginated_list(1, 10, SortOrder.DESC, "  joshua  ")

        query = self.collection.find.call_args.args[0]
        self.assertEqual(query["$or"][0]["name"]["$regex"], "joshua")

    def test_delete_booking_returns_true_when_deleted(self):
        self.collection.delete_one.return_value = SimpleNamespace(deleted_count=1)

        result = self.repo.delete_booking(VALID_OBJECT_ID)

        self.assertTrue(result)
        self.collection.delete_one.assert_called_once_with(
            {"_id": ObjectId(VALID_OBJECT_ID)}
        )

    def test_delete_booking_supports_legacy_string_ids(self):
        self.collection.delete_one.return_value = SimpleNamespace(deleted_count=0)

        result = self.repo.delete_booking("legacy-booking")

        self.assertFalse(result)
        self.collection.delete_one.assert_called_once_with(
            {"_id": "legacy-booking"}
        )

    def test_delete_all_returns_mongo_delete_result(self):
        result = SimpleNamespace(deleted_count=5)
        self.collection.delete_many.return_value = result

        returned = self.repo.delete_all()

        self.assertIs(returned, result)
        self.collection.delete_many.assert_called_once_with({})

    def test_count_by_ip_in_window_builds_datetime_query(self):
        self.collection.count_documents.return_value = 3

        result = self.repo.count_by_ip_in_window("203.0.113.5", 1700000000)

        self.assertEqual(result, 3)
        query = self.collection.count_documents.call_args.args[0]
        self.assertEqual(query["ip_address"], "203.0.113.5")
        self.assertEqual(
            query["created_at"]["$gte"], datetime.utcfromtimestamp(1700000000)
        )


if __name__ == "__main__":
    unittest.main()
