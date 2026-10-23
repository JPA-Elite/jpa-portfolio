import unittest
from unittest.mock import MagicMock

from app.Models.MusicLike import MusicLike
from app.Services.MusicLikeService import MusicLikeService
from tests.test_support import VALID_OBJECT_ID


class MusicLikeServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = MusicLikeService(repository=self.repo)

    def test_get_likes_count_requests_likes(self):
        self.repo.get_likes_count.return_value = 8

        result = self.service.get_likes_count("music-1")

        self.assertEqual(result, 8)
        self.repo.get_likes_count.assert_called_once_with("music-1", is_like=True)

    def test_get_dislikes_count_requests_dislikes(self):
        self.repo.get_likes_count.return_value = 3

        result = self.service.get_dislikes_count("music-1")

        self.assertEqual(result, 3)
        self.repo.get_likes_count.assert_called_once_with("music-1", is_like=False)

    def test_get_likes_counts_by_ids_requests_likes(self):
        self.repo.get_likes_counts_by_ids.return_value = {"m1": 2}

        result = self.service.get_likes_counts_by_ids(["m1", "m2"])

        self.assertEqual(result, {"m1": 2})
        self.repo.get_likes_counts_by_ids.assert_called_once_with(
            ["m1", "m2"], is_like=True
        )

    def test_get_dislikes_counts_by_ids_requests_dislikes(self):
        self.repo.get_likes_counts_by_ids.return_value = {"m1": 1}

        result = self.service.get_dislikes_counts_by_ids(["m1"])

        self.assertEqual(result, {"m1": 1})
        self.repo.get_likes_counts_by_ids.assert_called_once_with(
            ["m1"], is_like=False
        )

    def test_get_user_vote_normalizes_forwarded_ip(self):
        self.repo.get_user_vote.return_value = {"is_like": True}

        result = self.service.get_user_vote(
            "music-1", "203.0.113.5, 10.0.0.1"
        )

        self.assertEqual(result, {"is_like": True})
        self.repo.get_user_vote.assert_called_once_with("music-1", "203.0.113.5")

    def test_toggle_vote_adds_new_vote(self):
        self.repo.get_user_vote.return_value = None

        result = self.service.toggle_vote(
            "music-1", "203.0.113.5, 10.0.0.1", True
        )

        self.assertEqual(result, {"action": "added", "is_like": True})
        self.repo.get_user_vote.assert_called_once_with("music-1", "203.0.113.5")
        vote = self.repo.add_vote.call_args.args[0]
        self.assertIsInstance(vote, MusicLike)
        self.assertEqual(vote.music_id, "music-1")
        self.assertEqual(vote.ip_address, "203.0.113.5")
        self.assertTrue(vote.is_like)

    def test_toggle_vote_removes_matching_vote(self):
        self.repo.get_user_vote.return_value = {
            "_id": VALID_OBJECT_ID,
            "music_id": "music-1",
            "ip_address": "203.0.113.5",
            "is_like": True,
        }

        result = self.service.toggle_vote("music-1", "203.0.113.5", True)

        self.assertEqual(result, {"action": "removed", "is_like": True})
        self.repo.delete_vote.assert_called_once_with("music-1", "203.0.113.5")
        self.repo.update_vote.assert_not_called()
        self.repo.add_vote.assert_not_called()

    def test_toggle_vote_switches_opposite_vote(self):
        self.repo.get_user_vote.return_value = {
            "_id": VALID_OBJECT_ID,
            "music_id": "music-1",
            "ip_address": "203.0.113.5",
            "is_like": False,
        }

        result = self.service.toggle_vote("music-1", "203.0.113.5", True)

        self.assertEqual(result, {"action": "switched", "is_like": True})
        self.repo.update_vote.assert_called_once()
        vote = self.repo.update_vote.call_args.args[0]
        self.assertTrue(vote.is_like)
        self.repo.delete_vote.assert_not_called()
        self.repo.add_vote.assert_not_called()

    def test_toggle_vote_treats_empty_ip_as_is(self):
        self.repo.get_user_vote.return_value = None

        result = self.service.toggle_vote("music-1", "", False)

        self.assertEqual(result, {"action": "added", "is_like": False})
        self.repo.get_user_vote.assert_called_once_with("music-1", "")


if __name__ == "__main__":
    unittest.main()
