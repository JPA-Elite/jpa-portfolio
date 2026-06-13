import unittest
from unittest.mock import MagicMock

from app.Services.VlogLikeService import VlogLikeService
from tests.test_support import VALID_OBJECT_ID


class VlogLikeServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = VlogLikeService(repository=self.repo)

    def test_get_vlog_likes_count_by_id_returns_repository_count(self):
        self.repo.get_vlog_likes_count_by_id.return_value = 4

        result = self.service.get_vlog_likes_count_by_id("v1")

        self.assertEqual(result, 4)
        self.repo.get_vlog_likes_count_by_id.assert_called_once_with("v1")

    def test_get_vlog_likes_counts_by_ids_returns_repository_counts(self):
        self.repo.get_vlog_likes_counts_by_ids.return_value = {"v1": 4, "v2": 1}

        result = self.service.get_vlog_likes_counts_by_ids(["v1", "v2"])

        self.assertEqual(result, {"v1": 4, "v2": 1})
        self.repo.get_vlog_likes_counts_by_ids.assert_called_once_with(["v1", "v2"])

    def test_get_liked_states_normalizes_ip(self):
        self.repo.get_vlog_liked_states_by_ids_and_ip.return_value = {"v1": True}

        result = self.service.get_vlog_liked_states_by_ids_and_ip(["v1"], "127.0.0.1, 10.0.0.1")

        self.assertEqual(result, {"v1": True})
        self.repo.get_vlog_liked_states_by_ids_and_ip.assert_called_once_with(["v1"], "127.0.0.1")

    def test_get_vlog_likes_by_id_and_ip_returns_model(self):
        self.repo.get_vlog_likes_by_id_and_ip.return_value = {
            "_id": VALID_OBJECT_ID,
            "vlog_id": "v1",
            "ip_address": "127.0.0.1",
            "like": True,
        }

        result = self.service.get_vlog_likes_by_id_and_ip("v1", "127.0.0.1, 10.0.0.1")

        self.assertEqual(result.vlog_id, "v1")
        self.assertTrue(result.like)
        self.repo.get_vlog_likes_by_id_and_ip.assert_called_once_with("v1", "127.0.0.1", None)

    def test_add_vlog_like_normalizes_ip_and_saves_model(self):
        self.repo.add_vlog_like.return_value = "like-1"

        result = self.service.add_vlog_like({"vlog_id": "v1", "ip_address": "127.0.0.1, 10.0.0.1", "like": True})

        self.assertEqual(result, "like-1")
        saved = self.repo.add_vlog_like.call_args[0][0].to_dict()
        self.assertEqual(saved["vlog_id"], "v1")
        self.assertEqual(saved["ip_address"], "127.0.0.1")
        self.assertTrue(saved["like"])

    def test_toggle_vlog_like_updates_existing_like(self):
        self.repo.get_vlog_likes_by_id_and_ip.return_value = {
            "_id": VALID_OBJECT_ID,
            "vlog_id": "v1",
            "ip_address": "127.0.0.1",
            "like": True,
        }
        self.repo.update_vlog_like.return_value = True

        result = self.service.toggle_vlog_like("v1", "127.0.0.1")

        self.assertFalse(result["like"])
        self.assertTrue(result["updated"])
        updated_model = self.repo.update_vlog_like.call_args[0][0]
        self.assertFalse(updated_model.like)

    def test_toggle_vlog_like_creates_when_missing(self):
        self.repo.get_vlog_likes_by_id_and_ip.return_value = None
        self.repo.add_vlog_like.return_value = "new-like-id"

        result = self.service.toggle_vlog_like("v1", "127.0.0.1, 10.0.0.1")

        self.assertTrue(result["created"])
        self.assertTrue(result["like"])
        self.assertEqual(result["ip_address"], "127.0.0.1")
        self.repo.get_vlog_likes_by_id_and_ip.assert_called_once_with("v1", "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
