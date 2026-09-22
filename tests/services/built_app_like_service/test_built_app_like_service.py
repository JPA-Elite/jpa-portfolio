import unittest
from unittest.mock import MagicMock

from app.Services.BuiltAppLikeService import BuiltAppLikeService


class BuiltAppLikeServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = BuiltAppLikeService(repository=self.repo)

    def test_get_likes_count_returns_repository_value(self):
        self.repo.get_likes_count.return_value = 3

        result = self.service.get_likes_count("app1")

        self.assertEqual(result, 3)
        self.repo.get_likes_count.assert_called_once_with("app1", is_like=True)

    def test_get_dislikes_count_returns_repository_value(self):
        self.repo.get_likes_count.return_value = 2

        result = self.service.get_dislikes_count("app1")

        self.assertEqual(result, 2)
        self.repo.get_likes_count.assert_called_once_with("app1", is_like=False)

    def test_get_user_vote_strips_forwarded_ip_list(self):
        self.repo.get_user_vote.return_value = {"is_like": True}

        result = self.service.get_user_vote("app1", "10.0.0.1, 127.0.0.1")

        self.assertEqual(result, {"is_like": True})
        self.repo.get_user_vote.assert_called_once_with("app1", "10.0.0.1")

    def test_toggle_vote_adds_new_vote(self):
        self.repo.get_user_vote.return_value = None

        result = self.service.toggle_vote("app1", "127.0.0.1", True)

        self.assertEqual(result, {"action": "added", "is_like": True})
        self.repo.add_vote.assert_called_once()

    def test_toggle_vote_removes_same_vote(self):
        self.repo.get_user_vote.return_value = {
            "app_id": "app1",
            "ip_address": "127.0.0.1",
            "is_like": True,
        }

        result = self.service.toggle_vote("app1", "127.0.0.1", True)

        self.assertEqual(result, {"action": "removed", "is_like": True})
        self.repo.delete_vote.assert_called_once_with("app1", "127.0.0.1")
        self.repo.update_vote.assert_not_called()

    def test_toggle_vote_switches_opposite_vote(self):
        self.repo.get_user_vote.return_value = {
            "app_id": "app1",
            "ip_address": "127.0.0.1",
            "is_like": False,
        }

        result = self.service.toggle_vote("app1", "127.0.0.1", True)

        self.assertEqual(result, {"action": "switched", "is_like": True})
        self.repo.update_vote.assert_called_once()
        self.repo.delete_vote.assert_not_called()


if __name__ == "__main__":
    unittest.main()
