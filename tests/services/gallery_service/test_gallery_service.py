import unittest
from unittest.mock import MagicMock, patch

from backend.Services.GalleryService import GalleryService
from backend.configurations import SortOrder

from tests.services._service_fixtures import gallery_doc


class GalleryServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = GalleryService(repository=self.repo)

    def test_get_gallery_by_id_returns_repository_value(self):
        self.repo.get_gallery_by_id.return_value = gallery_doc()

        result = self.service.get_gallery_by_id("g1")

        self.assertEqual(result["id"], "g1")
        self.repo.get_gallery_by_id.assert_called_once_with("g1")

    def test_get_paginated_gallery_list_maps_gallery_models(self):
        self.repo.get_paginated_gallery_list.return_value = ([gallery_doc()], 1)

        items, total = self.service.get_paginated_gallery_list(1, 10, SortOrder.DESC)

        self.assertEqual(total, 1)
        self.assertEqual(items[0].id, "g1")
        self.assertEqual(items[0].title["en"], "Gallery")

    def test_add_gallery_without_file_saves_model(self):
        self.repo.add_gallery.return_value = "gallery-id"

        result = self.service.add_gallery(
            {"title": {"en": "New"}, "description": {"en": "Desc"}, "tags": ["a"]}
        )

        self.assertEqual(result, "gallery-id")
        saved = self.repo.add_gallery.call_args[0][0].to_dict()
        self.assertTrue(saved["id"])
        self.assertEqual(saved["image_url"], None)
        self.assertEqual(saved["tags"], ["a"])

    def test_update_gallery_returns_false_when_missing(self):
        self.repo.get_gallery_by_id.return_value = None

        result = self.service.update_gallery("g1", {"title": {"en": "Updated"}})

        self.assertFalse(result)
        self.repo.update_gallery.assert_not_called()

    def test_update_gallery_without_new_file_keeps_existing_image(self):
        self.repo.get_gallery_by_id.return_value = gallery_doc()
        self.repo.update_gallery.return_value = True

        result = self.service.update_gallery(
            "g1",
            {"title": {"en": "Updated"}, "description": {"en": "Updated Desc"}, "tags": ["x"]},
        )

        self.assertTrue(result)
        args = self.repo.update_gallery.call_args[0]
        self.assertEqual(args[0], "g1")
        updated = args[1].to_dict()
        self.assertEqual(updated["image_url"], "/img.jpg")
        self.assertEqual(updated["title"]["en"], "Updated")
        self.assertEqual(updated["tags"], ["x"])

    @patch("backend.Services.GalleryService.cleanup_uploaded_files")
    def test_delete_gallery_deletes_when_found(self, mock_cleanup):
        self.repo.get_gallery_by_id.return_value = gallery_doc()
        self.repo.delete_gallery.return_value = True

        result = self.service.delete_gallery("g1")

        self.assertTrue(result)
        mock_cleanup.assert_called_once_with(None, "/img.jpg")
        self.repo.delete_gallery.assert_called_once_with("g1")

    def test_search_gallery_paginated_maps_models(self):
        self.repo.search_gallery_paginated.return_value = ([gallery_doc()], 1)

        items, total = self.service.search_gallery_paginated("q", ["tag1"], "en", 1, 5, SortOrder.ASC)

        self.assertEqual(total, 1)
        self.assertEqual(items[1].description["en"], "Description")
        self.repo.search_gallery_paginated.assert_called_once_with("q", ["tag1"], "en", 1, 5, SortOrder.ASC)

    def test_get_all_tags_returns_repository_tags(self):
        self.repo.get_all_tags.return_value = ["a", "b"]

        result = self.service.get_all_tags(limit=10)

        self.assertEqual(result, ["a", "b"])
        self.repo.get_all_tags.assert_called_once_with(10)


if __name__ == "__main__":
    unittest.main()
