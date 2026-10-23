import unittest
from unittest.mock import MagicMock

from app.Services.ActivityLogService import ActivityLogService


class ActivityLogServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = ActivityLogService(repository=self.repo)

    def test_log_admin_activity_persists_normalized_entry(self):
        self.repo.insert.return_value = "log-1"

        result = self.service.log_admin_activity(
            {
                "_id": "507f1f77bcf86cd799439011",
                "method": "POST",
                "path": "/admin/api/add-gallery",
                "status_code": 201,
                "remote_addr": "203.0.113.5",
                "timestamp": "2026-10-23T12:00:00Z",
                "body": {"title": "Gallery"},
                "user_id": "user-1",
                "user": "admin",
                "duration_ms": 42,
            }
        )

        self.assertEqual(result, "log-1")
        entry = self.repo.insert.call_args.args[0]
        self.assertEqual(entry["_id"], "507f1f77bcf86cd799439011")
        self.assertEqual(entry["method"], "POST")
        self.assertEqual(entry["path"], "/admin/api/add-gallery")
        self.assertEqual(entry["status_code"], 201)
        self.assertEqual(entry["remote_addr"], "203.0.113.5")
        self.assertEqual(entry["timestamp"], "2026-10-23T12:00:00Z")
        self.assertEqual(entry["body"], {"title": "Gallery"})
        self.assertEqual(entry["user_id"], "user-1")
        self.assertEqual(entry["user"], "admin")
        self.assertEqual(entry["duration_ms"], 42)

    def test_log_admin_activity_omits_empty_optional_values(self):
        self.repo.insert.return_value = "log-2"

        self.service.log_admin_activity(
            {
                "method": "DELETE",
                "path": "/admin/api/delete-gallery/g1",
                "status_code": 200,
                "remote_addr": "127.0.0.1",
                "timestamp": "2026-10-23T12:00:00Z",
            }
        )

        entry = self.repo.insert.call_args.args[0]
        self.assertNotIn("body", entry)
        self.assertNotIn("user_id", entry)
        self.assertNotIn("user", entry)
        self.assertNotIn("_id", entry)

    def test_delete_by_ids_delegates_to_repository(self):
        self.repo.delete_by_ids.return_value = {
            "status": "success",
            "deleted_count": 2,
        }

        result = self.service.delete_by_ids(["a", "b"])

        self.assertEqual(result["deleted_count"], 2)
        self.repo.delete_by_ids.assert_called_once_with(["a", "b"])

    def test_delete_all_delegates_to_repository(self):
        self.repo.delete_all.return_value = {
            "status": "success",
            "deleted_count": 4,
        }

        result = self.service.delete_all()

        self.assertEqual(result["deleted_count"], 4)
        self.repo.delete_all.assert_called_once_with()

    def test_get_paginated_delegates_with_filters(self):
        self.repo.get_paginated.return_value = ([{"path": "/admin"}], 1)

        result = self.service.get_paginated(
            page=2, per_page=25, order="desc", search="gallery"
        )

        self.assertEqual(result, ([{"path": "/admin"}], 1))
        self.repo.get_paginated.assert_called_once_with(2, 25, "desc", "gallery")

    def test_find_recent_delegates_with_limit(self):
        self.repo.find_recent.return_value = [{"path": "/admin"}]

        result = self.service.find_recent(limit=12)

        self.assertEqual(result, [{"path": "/admin"}])
        self.repo.find_recent.assert_called_once_with(12)


if __name__ == "__main__":
    unittest.main()
