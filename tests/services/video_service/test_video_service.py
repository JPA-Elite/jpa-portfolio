import unittest
from unittest.mock import MagicMock, patch

from app.Services.VideoService import VideoService
from app.configurations import SortOrder

from tests.services._service_fixtures import video_doc


class VideoServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = VideoService(repository=self.repo)

    def test_get_video_by_id_returns_repository_value(self):
        self.repo.get_video_by_id.return_value = video_doc()

        result = self.service.get_video_by_id("v1")

        self.assertEqual(result["id"], "v1")
        self.repo.get_video_by_id.assert_called_once_with("v1")

    def test_get_paginated_video_list_maps_video_models(self):
        self.repo.get_paginated_video_list.return_value = ([video_doc()], 1)

        items, total = self.service.get_paginated_video_list(1, 10, SortOrder.DESC)

        self.assertEqual(total, 1)
        self.assertEqual(items[0].video_url, "/video.mp4")

    def test_add_video_without_file_saves_model(self):
        self.repo.add_video.return_value = "video-id"

        result = self.service.add_video(
            {"title": {"en": "New"}, "description": {"en": "Desc"}, "tags": ["tag1"]}
        )

        self.assertEqual(result, "video-id")
        saved = self.repo.add_video.call_args[0][0].to_dict()
        self.assertTrue(saved["id"])
        self.assertIsNone(saved["video_url"])
        self.assertEqual(saved["tags"], ["tag1"])

    def test_update_video_returns_false_when_missing(self):
        self.repo.get_video_by_id.return_value = None

        result = self.service.update_video("v1", {"title": {"en": "Updated"}})

        self.assertFalse(result)
        self.repo.update_video.assert_not_called()

    def test_update_video_without_new_file_keeps_existing_video_url(self):
        self.repo.get_video_by_id.return_value = video_doc()
        self.repo.update_video.return_value = True

        result = self.service.update_video(
            "v1",
            {"title": {"en": "Updated"}, "description": {"en": "Updated"}, "tags": ["x"]},
        )

        self.assertTrue(result)
        args = self.repo.update_video.call_args[0]
        self.assertEqual(args[0], "v1")
        updated = args[1].to_dict()
        self.assertEqual(updated["video_url"], "/video.mp4")
        self.assertEqual(updated["title"]["en"], "Updated")
        self.assertEqual(updated["tags"], ["x"])

    @patch("app.Services.VideoService.cleanup_uploaded_files")
    def test_delete_video_cleans_up_and_deletes(self, mock_cleanup):
        self.repo.get_video_by_id.return_value = video_doc()
        self.repo.delete_video.return_value = True

        result = self.service.delete_video("v1")

        self.assertTrue(result)
        mock_cleanup.assert_called_once_with("/video.mp4")
        self.repo.delete_video.assert_called_once_with("v1")

    def test_search_video_paginated_maps_models(self):
        self.repo.search_video_paginated.return_value = ([video_doc()], 1)

        items, total = self.service.search_video_paginated("q", ["tag1"], "en", 1, 5, SortOrder.ASC)

        self.assertEqual(total, 1)
        self.assertEqual(items[0].id, "v1")
        self.repo.search_video_paginated.assert_called_once_with("q", ["tag1"], "en", 1, 5, SortOrder.ASC)

    def test_get_all_tags_returns_repository_tags(self):
        self.repo.get_all_tags.return_value = ["tag1", "tag2"]

        result = self.service.get_all_tags(limit=5)

        self.assertEqual(result, ["tag1", "tag2"])
        self.repo.get_all_tags.assert_called_once_with(5)


if __name__ == "__main__":
    unittest.main()
