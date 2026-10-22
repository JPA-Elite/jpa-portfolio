import unittest
from unittest.mock import MagicMock, patch

from app.Services.VisitService import VisitService
from app.configurations import SortOrder
from app.constants.messages import DISPLAY_RECORDS_DELETE_MSG

from tests.services._service_fixtures import system_info_doc
from tests.test_support import VALID_OBJECT_ID


class VisitServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = VisitService(repository=self.repo)

    def test_get_paginated_system_info_maps_models(self):
        self.repo.get_paginated_documents.return_value = ([system_info_doc()], 1)

        items, total = self.service.get_paginated_system_info(1, 10, SortOrder.DESC)

        self.assertEqual(total, 1)
        self.assertEqual(items[0].system, "Windows")
        self.repo.get_paginated_documents.assert_called_once_with(1, 10, SortOrder.DESC, "")

    def test_get_paginated_system_info_forwards_search(self):
        self.repo.get_paginated_documents.return_value = ([system_info_doc()], 1)

        items, total = self.service.get_paginated_system_info(2, 5, SortOrder.ASC, "chrome")

        self.assertEqual(total, 1)
        self.assertEqual(items[0].page, "/profile")
        self.repo.get_paginated_documents.assert_called_once_with(2, 5, SortOrder.ASC, "chrome")

    @patch("app.Services.VisitService.delete_image_from_cloudinary")
    def test_delete_page_system_info_deletes_records_and_images(self, mock_delete_cloudinary):
        records = [
            {"_id": VALID_OBJECT_ID, "image_capture": "https://res.cloudinary.com/demo/image/upload/v1/test.png"}
        ]

        result = self.service.delete_page_system_info(records)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], DISPLAY_RECORDS_DELETE_MSG)
        self.repo.delete_system_info_by_id.assert_called_once()
        mock_delete_cloudinary.assert_called_once()

    def test_count_visits_returns_repository_count(self):
        self.repo.count_visits.return_value = 42

        result = self.service.count_visits({"page": "/profile"})

        self.assertEqual(result, 42)
        self.repo.count_visits.assert_called_once_with({"page": "/profile"})

    @patch("app.Services.VisitService.delete_image_from_cloudinary")
    def test_delete_all_visitors_cleans_images_and_returns_repository_result(self, mock_delete_cloudinary):
        self.repo.find_all_image_captures.return_value = [
            "https://res.cloudinary.com/demo/image/upload/v1/one.png",
            None,
            "https://res.cloudinary.com/demo/image/upload/v1/two.png",
        ]
        self.repo.delete_all_visitors.return_value = {
            "status": "success",
            "message": "Deleted 2 visitor record(s).",
            "deleted_count": 2,
        }

        result = self.service.delete_all_visitors()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["deleted_count"], 2)
        self.repo.delete_all_visitors.assert_called_once_with()
        self.assertEqual(mock_delete_cloudinary.call_count, 2)

    @patch("app.Services.VisitService.delete_image_from_cloudinary")
    def test_delete_all_visitors_normalizes_boolean_repository_result(self, mock_delete_cloudinary):
        self.repo.find_all_image_captures.return_value = ["https://res.cloudinary.com/demo/image/upload/v1/one.png"]
        self.repo.delete_all_visitors.return_value = True

        result = self.service.delete_all_visitors()

        self.assertEqual(result["status"], "success")
        mock_delete_cloudinary.assert_called_once()

    @patch("app.Services.VisitService.delete_image_from_cloudinary")
    def test_delete_all_visitors_skips_image_cleanup_on_repository_error(self, mock_delete_cloudinary):
        self.repo.find_all_image_captures.return_value = ["https://res.cloudinary.com/demo/image/upload/v1/one.png"]
        self.repo.delete_all_visitors.return_value = {"status": "error", "message": "boom"}

        result = self.service.delete_all_visitors()

        self.assertEqual(result["status"], "error")
        mock_delete_cloudinary.assert_not_called()

    def test_delete_all_visitors_returns_error_when_repository_raises(self):
        self.repo.find_all_image_captures.side_effect = RuntimeError("boom")

        result = self.service.delete_all_visitors()

        self.assertEqual(result["status"], "error")
        self.assertIn("boom", result["message"])


if __name__ == "__main__":
    unittest.main()
