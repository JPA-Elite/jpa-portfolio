import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.Repositories.ActivityLogRepository import ActivityLogRepository
from app.Repositories.BaseRepository import BaseRepository
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


class ActivityLogRepositoryTests(unittest.TestCase):
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
        self.repo = ActivityLogRepository()

    def test_insert_delegates_to_insert_one(self):
        self.collection.insert_one.return_value = SimpleNamespace(
            inserted_id=VALID_OBJECT_ID
        )
        entry = {
            "method": "POST",
            "path": "/admin/api/add-gallery",
            "status_code": 200,
        }

        result = self.repo.insert(entry)

        self.assertEqual(result.inserted_id, VALID_OBJECT_ID)
        self.collection.insert_one.assert_called_once_with(entry)

    def test_delete_by_ids_with_empty_list_clears_all_activity(self):
        self.collection.delete_many.return_value = SimpleNamespace(deleted_count=4)

        result = self.repo.delete_by_ids([])

        self.assertEqual(
            result, {"status": "success", "deleted_count": 4}
        )
        self.collection.delete_many.assert_called_once_with({})

    def test_delete_by_ids_uses_object_ids_for_valid_values(self):
        self.collection.delete_many.return_value = SimpleNamespace(deleted_count=2)

        result = self.repo.delete_by_ids(
            [VALID_OBJECT_ID, "507f1f77bcf86cd799439012"]
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["deleted_count"], 2)
        query = self.collection.delete_many.call_args.args[0]
        expected_ids = [
            ObjectId(VALID_OBJECT_ID),
            ObjectId("507f1f77bcf86cd799439012"),
        ]
        self.assertEqual(query, {"_id": {"$in": expected_ids}})

    def test_delete_by_ids_ignores_invalid_ids_when_valid_ids_exist(self):
        self.collection.delete_many.return_value = SimpleNamespace(deleted_count=1)

        result = self.repo.delete_by_ids([VALID_OBJECT_ID, "not-an-object-id"])

        self.assertEqual(result["status"], "success")
        query = self.collection.delete_many.call_args.args[0]
        self.assertEqual(query, {"_id": {"$in": [ObjectId(VALID_OBJECT_ID)]}})

    def test_delete_by_ids_rejects_only_invalid_ids(self):
        result = self.repo.delete_by_ids(["not-an-object-id", None])

        self.assertEqual(
            result, {"status": "error", "message": "Invalid record IDs."}
        )
        self.collection.delete_many.assert_not_called()

    def test_delete_by_ids_reports_missing_records(self):
        self.collection.delete_many.return_value = SimpleNamespace(deleted_count=0)

        result = self.repo.delete_by_ids([VALID_OBJECT_ID])

        self.assertEqual(
            result,
            {"status": "error", "message": "Activity record not found."},
        )

    def test_delete_all_returns_deleted_count(self):
        self.collection.delete_many.return_value = SimpleNamespace(deleted_count=3)

        result = self.repo.delete_all()

        self.assertEqual(result, {"status": "success", "deleted_count": 3})
        self.collection.delete_many.assert_called_once_with({})

    def test_count_by_query_returns_integer(self):
        self.collection.count_documents.return_value = 7

        result = self.repo.count_by_query({"method": "POST"})

        self.assertEqual(result, 7)
        self.collection.count_documents.assert_called_once_with({"method": "POST"})

    def test_count_by_query_treats_none_as_empty_query(self):
        self.collection.count_documents.return_value = 2

        result = self.repo.count_by_query(None)

        self.assertEqual(result, 2)
        self.collection.count_documents.assert_called_once_with({})

    def test_find_recent_sorts_and_limits_and_stringifies_ids(self):
        cursor = _RecordingCursor(
            [{"_id": ObjectId(VALID_OBJECT_ID), "path": "/admin"}]
        )
        self.collection.find.return_value = cursor

        result = self.repo.find_recent(limit=12)

        self.assertEqual(result[0]["_id"], VALID_OBJECT_ID)
        self.collection.find.assert_called_once_with({}, {})
        self.assertEqual(cursor.sort_calls[0][0], ([("_id", -1)],))
        self.assertEqual(cursor.limit_calls[0][0], (12,))

    def test_get_paginated_returns_empty_when_no_records_match(self):
        self.collection.count_documents.return_value = 0

        result = self.repo.get_paginated(page=2, per_page=10, search="missing")

        self.assertEqual(result, ([], 0))
        self.collection.find.assert_not_called()

    def test_get_paginated_applies_pagination_sort_and_projection(self):
        cursor = _RecordingCursor(
            [{"_id": ObjectId(VALID_OBJECT_ID), "path": "/admin"}]
        )
        self.collection.find.return_value = cursor
        self.collection.count_documents.return_value = 6

        docs, total = self.repo.get_paginated(
            page=2,
            per_page=3,
            order=SortOrder.DESC,
            search="admin",
        )

        self.assertEqual(total, 6)
        self.assertEqual(docs[0]["_id"], VALID_OBJECT_ID)
        self.assertEqual(cursor.skip_calls[0][0], (3,))
        self.assertEqual(cursor.limit_calls[0][0], (3,))
        self.assertEqual(cursor.sort_calls[0][0], ([("_id", -1)],))
        query = self.collection.count_documents.call_args.args[0]
        self.assertEqual(query["$or"][1], {"path": {"$regex": "admin", "$options": "i"}})
        self.assertEqual(
            self.collection.find.call_args.args[1]["status_code"], 1
        )

    def test_get_paginated_clamps_page_and_per_page(self):
        cursor = _RecordingCursor([])
        self.collection.find.return_value = cursor
        self.collection.count_documents.return_value = 1

        self.repo.get_paginated(page=0, per_page=500)

        self.assertEqual(cursor.skip_calls, [])
        self.assertEqual(cursor.limit_calls[0][0], (100,))

    def test_get_paginated_normalizes_invalid_page_values(self):
        cursor = _RecordingCursor([])
        self.collection.find.return_value = cursor
        self.collection.count_documents.return_value = 1

        self.repo.get_paginated(page="bad", per_page="bad")

        self.assertEqual(cursor.skip_calls, [])
        self.assertEqual(cursor.limit_calls[0][0], (10,))

    def test_get_paginated_uses_ascending_sort_by_default(self):
        cursor = _RecordingCursor([])
        self.collection.find.return_value = cursor
        self.collection.count_documents.return_value = 1

        self.repo.get_paginated(order=SortOrder.ASC)

        self.assertEqual(cursor.sort_calls[0][0], ([("_id", 1)],))

    def test_build_search_query_is_empty_for_blank_search(self):
        self.assertEqual(self.repo.build_search_query("   "), {})

    def test_build_search_query_escapes_regex_and_searches_all_fields(self):
        query = self.repo.build_search_query("ad.min")

        self.assertEqual(len(query["$or"]), 5)
        self.assertEqual(
            query["$or"][0],
            {"method": {"$regex": "ad\\.min", "$options": "i"}},
        )
        self.assertEqual(
            query["$or"][1],
            {"path": {"$regex": "ad\\.min", "$options": "i"}},
        )
        self.assertEqual(
            query["$or"][2],
            {"user_id": {"$regex": "ad\\.min", "$options": "i"}},
        )
        self.assertEqual(
            query["$or"][3],
            {"remote_addr": {"$regex": "ad\\.min", "$options": "i"}},
        )
        self.assertEqual(
            query["$or"][4],
            {"timestamp": {"$regex": "ad\\.min", "$options": "i"}},
        )


if __name__ == "__main__":
    unittest.main()
