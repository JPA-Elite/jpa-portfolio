import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.Models.MusicLike import MusicLike
from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.MusicLikeRepository import MusicLikeRepository
from tests.test_support import VALID_OBJECT_ID


class MusicLikeRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.collection = MagicMock()
        self.patcher = patch.object(
            BaseRepository,
            "get_mongo_client",
            new=lambda repository, collection_name: (
                object(),
                {},
                self.collection,
            ),
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.repo = MusicLikeRepository()

    def test_get_likes_count_filters_by_music_and_like_value(self):
        self.collection.count_documents.return_value = 6

        result = self.repo.get_likes_count("music-1", is_like=True)

        self.assertEqual(result, 6)
        self.collection.count_documents.assert_called_once_with(
            {"music_id": "music-1", "is_like": True}
        )

    def test_get_dislikes_count_reuses_like_count_with_false(self):
        self.collection.count_documents.return_value = 2

        result = self.repo.get_dislikes_count("music-1")

        self.assertEqual(result, 2)
        self.collection.count_documents.assert_called_once_with(
            {"music_id": "music-1", "is_like": False}
        )

    def test_get_likes_counts_by_ids_returns_empty_without_ids(self):
        result = self.repo.get_likes_counts_by_ids([])

        self.assertEqual(result, {})
        self.collection.aggregate.assert_not_called()

    def test_get_likes_counts_by_ids_groups_counts(self):
        self.collection.aggregate.return_value = [
            {"_id": "music-1", "count": 4},
            {"_id": "music-2", "count": 1},
            {"_id": "music-3"},
        ]

        result = self.repo.get_likes_counts_by_ids(
            ["music-1", "music-2", "music-3"], is_like=False
        )

        self.assertEqual(
            result, {"music-1": 4, "music-2": 1, "music-3": 0}
        )
        pipeline = self.collection.aggregate.call_args.args[0]
        self.assertEqual(
            pipeline[0],
            {
                "$match": {
                    "music_id": {"$in": ["music-1", "music-2", "music-3"]},
                    "is_like": False,
                }
            },
        )
        self.assertEqual(
            pipeline[1], {"$group": {"_id": "$music_id", "count": {"$sum": 1}}}
        )
        self.assertEqual(
            self.collection.aggregate.call_args.kwargs, {"allowDiskUse": False}
        )

    def test_get_user_vote_returns_none_without_ip(self):
        self.assertIsNone(self.repo.get_user_vote("music-1", ""))
        self.assertIsNone(self.repo.get_user_vote("music-1", None))
        self.collection.find_one.assert_not_called()

    def test_get_user_vote_matches_any_forwarded_ip(self):
        self.collection.find_one.return_value = {
            "_id": ObjectId(VALID_OBJECT_ID),
            "music_id": "music-1",
            "is_like": True,
        }

        result = self.repo.get_user_vote(
            "music-1", "203.0.113.5, 10.0.0.1"
        )

        self.assertTrue(result["is_like"])
        query = self.collection.find_one.call_args.args[0]
        self.assertEqual(len(query["$or"]), 2)
        self.assertEqual(
            query["$or"][0],
            {
                "music_id": "music-1",
                "ip_address": {
                    "$regex": r"(^|[,\s]+)203\.0\.113\.5([,\s]+|$)",
                    "$options": "i",
                },
            },
        )
        self.assertEqual(
            query["$or"][1]["ip_address"]["$regex"],
            r"(^|[,\s]+)10\.0\.0\.1([,\s]+|$)",
        )
        self.collection.find_one.assert_called_once_with(query, None)

    def test_get_user_vote_ignores_empty_parts_of_ip_header(self):
        self.repo.get_user_vote("music-1", " ,  , ")

        self.collection.find_one.assert_not_called()

    def test_add_vote_inserts_model_and_returns_string_id(self):
        self.collection.insert_one.return_value = SimpleNamespace(
            inserted_id=ObjectId(VALID_OBJECT_ID)
        )
        vote = MusicLike("music-1", "203.0.113.5", is_like=True)

        result = self.repo.add_vote(vote)

        self.assertEqual(result, VALID_OBJECT_ID)
        self.collection.insert_one.assert_called_once_with(
            {
                "music_id": "music-1",
                "ip_address": "203.0.113.5",
                "is_like": True,
            }
        )

    def test_update_vote_returns_true_when_modified(self):
        self.collection.update_one.return_value = SimpleNamespace(modified_count=1)
        vote = MusicLike("music-1", "203.0.113.5", is_like=False)

        result = self.repo.update_vote(vote)

        self.assertTrue(result)
        self.collection.update_one.assert_called_once_with(
            {"music_id": "music-1", "ip_address": "203.0.113.5"},
            {"$set": {"is_like": False}},
            upsert=False,
        )

    def test_update_vote_returns_false_when_not_modified(self):
        self.collection.update_one.return_value = SimpleNamespace(modified_count=0)

        result = self.repo.update_vote(
            MusicLike("music-1", "203.0.113.5", is_like=True)
        )

        self.assertFalse(result)

    def test_delete_vote_returns_true_when_deleted(self):
        self.collection.delete_one.return_value = SimpleNamespace(deleted_count=1)

        result = self.repo.delete_vote("music-1", "203.0.113.5")

        self.assertTrue(result)
        self.collection.delete_one.assert_called_once_with(
            {"music_id": "music-1", "ip_address": "203.0.113.5"}
        )

    def test_delete_vote_returns_false_when_missing(self):
        self.collection.delete_one.return_value = SimpleNamespace(deleted_count=0)

        result = self.repo.delete_vote("music-1", "203.0.113.5")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
