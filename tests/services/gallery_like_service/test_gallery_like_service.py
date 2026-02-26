import unittest
from unittest.mock import MagicMock

from backend.Services.GalleryLikeService import GalleryLikeService
from tests.test_support import VALID_OBJECT_ID


class GalleryLikeServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = GalleryLikeService(repository=self.repo)

    def test_get_gallery_likes_count_by_id_returns_repository_count(self):
        self.repo.get_gallery_likes_count_by_id.return_value = 5

        result = self.service.get_gallery_likes_count_by_id("g-1")

        self.assertEqual(result, 5)
        self.repo.get_gallery_likes_count_by_id.assert_called_once_with("g-1")

    def test_get_gallery_likes_by_id_and_ip_returns_none_when_not_found(self):
        self.repo.get_gallery_likes_by_id_and_ip.return_value = None

        result = self.service.get_gallery_likes_by_id_and_ip("g-1", "127.0.0.1, 10.0.0.1")

        self.assertIsNone(result)
        self.repo.get_gallery_likes_by_id_and_ip.assert_called_once_with("g-1", "127.0.0.1", None)

    def test_get_gallery_likes_by_id_and_ip_maps_model(self):
        self.repo.get_gallery_likes_by_id_and_ip.return_value = {
            "_id": VALID_OBJECT_ID,
            "gallery_id": "g-1",
            "ip_address": "127.0.0.1",
            "like": True,
        }

        result = self.service.get_gallery_likes_by_id_and_ip("g-1", "127.0.0.1")

        self.assertEqual(result.gallery_id, "g-1")
        self.assertTrue(result.like)

    def test_add_gallery_like_normalizes_ip_and_saves_model(self):
        self.repo.add_gallery_like.return_value = "like-1"

        result = self.service.add_gallery_like(
            {"gallery_id": "g-1", "ip_address": "127.0.0.1, 10.0.0.1", "like": True}
        )

        self.assertEqual(result, "like-1")
        saved = self.repo.add_gallery_like.call_args[0][0].to_dict()
        self.assertEqual(saved["gallery_id"], "g-1")
        self.assertEqual(saved["ip_address"], "127.0.0.1")
        self.assertTrue(saved["like"])

    def test_toggle_gallery_like_updates_existing_like(self):
        self.repo.get_gallery_likes_by_id_and_ip.return_value = {
            "_id": VALID_OBJECT_ID,
            "gallery_id": "g-1",
            "ip_address": "127.0.0.1",
            "like": True,
        }
        self.repo.update_gallery_like.return_value = True

        result = self.service.toggle_gallery_like("g-1", "127.0.0.1")

        self.assertFalse(result["like"])
        self.assertTrue(result["updated"])
        updated_model = self.repo.update_gallery_like.call_args[0][0]
        self.assertFalse(updated_model.like)

    def test_toggle_gallery_like_creates_new_like_and_normalizes_ip(self):
        self.repo.get_gallery_likes_by_id_and_ip.return_value = None
        self.repo.add_gallery_like.return_value = "like-1"

        result = self.service.toggle_gallery_like("g-1", "127.0.0.1, 10.0.0.1")

        self.assertTrue(result["like"])
        self.assertTrue(result["created"])
        self.assertEqual(result["ip_address"], "127.0.0.1")
        self.repo.get_gallery_likes_by_id_and_ip.assert_called_once_with("g-1", "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
