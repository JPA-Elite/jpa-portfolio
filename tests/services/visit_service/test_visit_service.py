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
        self.repo.get_paginated_documents.assert_called_once_with(1, 10, SortOrder.DESC)

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


if __name__ == "__main__":
    unittest.main()
