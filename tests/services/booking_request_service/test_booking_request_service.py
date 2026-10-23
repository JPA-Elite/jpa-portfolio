import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.Services.BookingRequestService import BookingRequestService


class BookingRequestServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = BookingRequestService(repository=self.repo)

    def _doc(self, **overrides):
        doc = {
            "_id": "booking-1",
            "name": "Joshua",
            "email": "joshua@example.com",
            "preferred_date": "2026-11-02",
            "preferred_time": "13:05",
            "message": "Project discussion",
            "ip_address": "203.0.113.5",
            "created_at": datetime(2026, 10, 23, 4, 30),
            "read": False,
            "service": "Consultation",
        }
        doc.update(overrides)
        return doc

    def test_get_paginated_list_converts_docs_and_philippine_time(self):
        self.repo.get_paginated_list.return_value = ([self._doc()], 3)

        items, total = self.service.get_paginated_list(
            page=2, per_page=5, order="desc", search_query="joshua"
        )

        self.assertEqual(total, 3)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, "Joshua")
        self.assertEqual(items[0].service, "Consultation")
        self.assertEqual(items[0]._display_created, "2026-10-23 12:30 PM")
        self.repo.get_paginated_list.assert_called_once_with(
            2, 5, "desc", "joshua"
        )

    def test_get_paginated_list_parses_iso_created_at_string(self):
        doc = self._doc(created_at="2026-10-23T04:30:00")
        self.repo.get_paginated_list.return_value = ([doc], 1)

        items, _total = self.service.get_paginated_list(1, 10, "desc")

        self.assertEqual(items[0]._display_created, "2026-10-23 12:30 PM")

    def test_get_by_id_returns_model_when_found(self):
        self.repo.find_by_id.return_value = self._doc()

        item = self.service.get_by_id("booking-1")

        self.assertEqual(item.name, "Joshua")
        self.assertEqual(item._id, "booking-1")
        self.repo.find_by_id.assert_called_once_with("booking-1")

    def test_get_by_id_returns_none_when_missing(self):
        self.repo.find_by_id.return_value = None

        self.assertIsNone(self.service.get_by_id("missing"))
        self.repo.find_by_id.assert_called_once_with("missing")

    def test_delete_booking_deletes_existing_record(self):
        self.repo.find_by_id.return_value = self._doc()
        self.repo.delete_booking.return_value = True

        result = self.service.delete_booking("booking-1")

        self.assertTrue(result)
        self.repo.delete_booking.assert_called_once_with("booking-1")

    def test_delete_booking_returns_false_when_missing(self):
        self.repo.find_by_id.return_value = None

        result = self.service.delete_booking("missing")

        self.assertFalse(result)
        self.repo.delete_booking.assert_not_called()

    def test_delete_booking_returns_repository_result(self):
        self.repo.find_by_id.return_value = self._doc()
        self.repo.delete_booking.return_value = False

        self.assertFalse(self.service.delete_booking("booking-1"))

    def test_delete_all_booking_requests_returns_count(self):
        self.repo.delete_all.return_value = SimpleNamespace(deleted_count=3)

        result = self.service.delete_all_booking_requests()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["deleted_count"], 3)
        self.assertIn("3", result["message"])

    def test_delete_all_booking_requests_handles_zero_deleted(self):
        self.repo.delete_all.return_value = SimpleNamespace(deleted_count=0)

        result = self.service.delete_all_booking_requests()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["deleted_count"], 0)
        self.assertIn("0", result["message"])

    def test_delete_all_booking_requests_returns_error_on_failure(self):
        self.repo.delete_all.side_effect = RuntimeError("db down")

        result = self.service.delete_all_booking_requests()

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "db down")


if __name__ == "__main__":
    unittest.main()
