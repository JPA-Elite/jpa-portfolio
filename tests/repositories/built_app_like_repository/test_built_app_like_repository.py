import unittest
from unittest.mock import patch

from app.Models.BuiltAppLike import BuiltAppLike
from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.BuiltAppLikeRepository import BuiltAppLikeRepository
from tests.repositories.shared._repository_test_helpers import _fake_get_mongo_client


class BuiltAppLikeRepositoryTests(unittest.TestCase):
    def _make_repo(self):
        patcher = patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client)
        patcher.start()
        self.addCleanup(patcher.stop)
        return BuiltAppLikeRepository()

    def test_smoke_instantiation(self):
        repo = self._make_repo()
        self.assertTrue(hasattr(repo, "collection"))

    def test_counts_return_int(self):
        repo = self._make_repo()
        self.assertIsInstance(repo.get_likes_count("app1"), int)
        self.assertIsInstance(repo.get_dislikes_count("app1"), int)

    def test_get_user_vote_returns_doc_or_none(self):
        repo = self._make_repo()
        result = repo.get_user_vote("app1", "127.0.0.1")
        self.assertTrue(result is None or isinstance(result, dict))
        self.assertIsNone(repo.get_user_vote("app1", ""))

    def test_add_update_delete_vote(self):
        repo = self._make_repo()
        vote = BuiltAppLike(app_id="app1", ip_address="127.0.0.1", is_like=True)
        self.assertIsInstance(repo.add_vote(vote), str)
        self.assertTrue(repo.update_vote(vote))
        self.assertTrue(repo.delete_vote("app1", "127.0.0.1"))


if __name__ == "__main__":
    unittest.main()
