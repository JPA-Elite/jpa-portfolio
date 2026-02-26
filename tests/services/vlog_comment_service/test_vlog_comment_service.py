import unittest
from unittest.mock import MagicMock

from backend.Services.VlogCommentService import VlogCommentService

from tests.services._service_fixtures import comment_doc
from tests.test_support import VALID_OBJECT_ID


class VlogCommentServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = VlogCommentService(repository=self.repo)

    def test_count_comments_by_vlog_returns_repository_count(self):
        self.repo.count_comments_by_vlog.return_value = 2

        result = self.service.count_comments_by_vlog("v1")

        self.assertEqual(result, 2)
        self.repo.count_comments_by_vlog.assert_called_once_with("v1")

    def test_count_comments_by_vlog_ids_returns_repository_counts(self):
        self.repo.count_comments_by_vlog_ids.return_value = {"v1": 2, "v2": 1}

        result = self.service.count_comments_by_vlog_ids(["v1", "v2"])

        self.assertEqual(result, {"v1": 2, "v2": 1})
        self.repo.count_comments_by_vlog_ids.assert_called_once_with(["v1", "v2"])

    def test_get_comments_marks_current_user_like(self):
        self.repo.find__paginate_comments_by_vlog.return_value = [comment_doc("vlog_id")]
        self.repo.count_comments_by_vlog.return_value = 1

        comments, total = self.service.get_comments("v1", "127.0.0.1, 10.0.0.1", 1, 10)

        self.assertEqual(total, 1)
        self.assertTrue(comments[0]["is_liked"])
        self.repo.find__paginate_comments_by_vlog.assert_called_once_with("v1", 1, 10)

    def test_add_comment_normalizes_ip_and_saves_model(self):
        self.repo.add_comment.return_value = "comment-1"

        result = self.service.add_comment("v1", "127.0.0.1, 10.0.0.1", "Hello")

        self.assertEqual(result, "comment-1")
        saved = self.repo.add_comment.call_args[0][0].to_dict()
        self.assertEqual(saved["vlog_id"], "v1")
        self.assertEqual(saved["ip_address"], "127.0.0.1")
        self.assertEqual(saved["author_name"], "user_127.0.0.1")

    def test_toggle_like_adds_ip(self):
        self.repo.find_by_id.return_value = {"_id": VALID_OBJECT_ID, "liked_ips": []}

        result = self.service.toggle_like("comment-1", "127.0.0.1, 10.0.0.1")

        self.assertTrue(result["liked"])
        self.assertEqual(result["like_count"], 1)
        saved_comment = self.repo.update_comment.call_args[0][0]
        self.assertEqual(saved_comment["liked_ips"], ["127.0.0.1"])


if __name__ == "__main__":
    unittest.main()
