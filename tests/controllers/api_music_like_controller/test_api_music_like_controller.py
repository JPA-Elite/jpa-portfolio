import importlib
import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

from app.Repositories.BaseRepository import BaseRepository


def _fake_get_mongo_client(self, collection_name):
    return object(), {}, MagicMock()


class ApiMusicLikeControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client):
            cls.module = importlib.import_module(
                "app.Controllers.api.MusicLikeController"
            )

    def setUp(self):
        self.service = MagicMock()
        self.service_patcher = patch.object(
            self.module, "music_like_service", self.service
        )
        self.service_patcher.start()
        self.addCleanup(self.service_patcher.stop)

        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"
        self.app.add_url_rule(
            "/api/music-like/counts",
            endpoint="music_like_counts",
            view_func=self.module.music_like_counts_route,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/api/music-like/counts/batch",
            endpoint="music_like_counts_batch",
            view_func=self.module.music_like_counts_batch_route,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/api/music-like/vote",
            endpoint="music_toggle_vote",
            view_func=self.module.music_toggle_vote_route,
            methods=["POST"],
        )
        self.client = self.app.test_client()

    def test_counts_returns_like_dislike_and_user_vote(self):
        self.service.get_likes_count.return_value = 7
        self.service.get_dislikes_count.return_value = 2
        self.service.get_user_vote.return_value = {"is_like": True}

        response = self.client.get(
            "/api/music-like/counts?music_id=music-1",
            headers={"X-Forwarded-For": "10.0.0.1, 10.0.0.2"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"like_counts": 7, "dislike_counts": 2, "user_vote": True},
        )
        self.service.get_likes_count.assert_called_once_with("music-1")
        self.service.get_dislikes_count.assert_called_once_with("music-1")
        self.service.get_user_vote.assert_called_once_with(
            "music-1", "10.0.0.1, 10.0.0.2"
        )

    def test_counts_uses_remote_address_without_forwarded_header(self):
        self.service.get_likes_count.return_value = 0
        self.service.get_dislikes_count.return_value = 0
        self.service.get_user_vote.return_value = None

        response = self.client.get(
            "/api/music-like/counts?music_id=music-1",
            environ_overrides={"REMOTE_ADDR": "127.0.0.9"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get_json()["user_vote"])
        self.service.get_user_vote.assert_called_once_with("music-1", "127.0.0.9")

    def test_batch_returns_counts_and_votes_for_each_music(self):
        self.service.get_likes_counts_by_ids.return_value = {"m1": 4, "m2": 0}
        self.service.get_dislikes_counts_by_ids.return_value = {"m1": 1, "m2": 3}
        self.service.get_user_vote.side_effect = [{"is_like": False}, None]

        response = self.client.get(
            "/api/music-like/counts/batch?music_ids=m1,m2",
            headers={"X-Forwarded-For": "10.0.0.5"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "items": {
                    "m1": {
                        "like_counts": 4,
                        "dislike_counts": 1,
                        "user_vote": False,
                    },
                    "m2": {
                        "like_counts": 0,
                        "dislike_counts": 3,
                        "user_vote": None,
                    },
                }
            },
        )
        self.service.get_likes_counts_by_ids.assert_called_once_with(["m1", "m2"])
        self.service.get_dislikes_counts_by_ids.assert_called_once_with(["m1", "m2"])

    def test_batch_returns_empty_items_without_music_ids(self):
        response = self.client.get("/api/music-like/counts/batch?music_ids=")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"items": {}})
        self.service.get_likes_counts_by_ids.assert_not_called()
        self.service.get_dislikes_counts_by_ids.assert_not_called()

    def test_batch_limits_music_ids_to_fifty(self):
        music_ids = [f"m{index}" for index in range(60)]
        self.service.get_likes_counts_by_ids.return_value = {}
        self.service.get_dislikes_counts_by_ids.return_value = {}
        self.service.get_user_vote.return_value = None

        response = self.client.get(
            "/api/music-like/counts/batch?music_ids=" + ",".join(music_ids),
            headers={"X-Forwarded-For": "10.0.0.5"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["items"]), 50)
        self.service.get_likes_counts_by_ids.assert_called_once_with(music_ids[:50])

    def test_toggle_requires_music_id(self):
        response = self.client.post(
            "/api/music-like/vote", json={"is_like": True}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.get_json())
        self.service.toggle_vote.assert_not_called()

    def test_toggle_uses_explicit_false_like_value(self):
        self.service.toggle_vote.return_value = {
            "action": "added",
            "is_like": False,
        }

        response = self.client.post(
            "/api/music-like/vote",
            json={"music_id": "m1", "is_like": False},
            headers={"X-Forwarded-For": "10.0.0.1, 10.0.0.2"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "message": "Vote updated",
                "data": {"action": "added", "is_like": False},
            },
        )
        self.service.toggle_vote.assert_called_once_with(
            "m1", "10.0.0.1, 10.0.0.2", False
        )

    def test_toggle_defaults_to_like_when_value_is_omitted(self):
        self.service.toggle_vote.return_value = {"action": "added", "is_like": True}

        response = self.client.post(
            "/api/music-like/vote",
            json={"music_id": "m1"},
            headers={"X-Forwarded-For": "10.0.0.1"},
        )

        self.assertEqual(response.status_code, 200)
        self.service.toggle_vote.assert_called_once_with(
            "m1", "10.0.0.1", True
        )

    def test_toggle_parses_string_false_as_false(self):
        self.service.toggle_vote.return_value = {"action": "switched", "is_like": False}

        response = self.client.post(
            "/api/music-like/vote",
            json={"music_id": "m1", "is_like": "false"},
            headers={"X-Forwarded-For": "10.0.0.1"},
        )

        self.assertEqual(response.status_code, 200)
        self.service.toggle_vote.assert_called_once_with(
            "m1", "10.0.0.1", False
        )


if __name__ == "__main__":
    unittest.main()
