import unittest
from unittest.mock import MagicMock

from app.Services.VlogCommentService import VlogCommentService

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
        self.assertTrue(comments[0]["is_own"])
        self.repo.find__paginate_comments_by_vlog.assert_called_once_with("v1", 1, 10)

    def test_get_comments_overrides_name_with_saved_display_name(self):
        self.repo.find__paginate_comments_by_vlog.return_value = [comment_doc("vlog_id")]
        self.repo.count_comments_by_vlog.return_value = 1
        name_service = MagicMock()
        name_service.get_profiles_map.return_value = {
            "127.0.0.1": {"display_name": "Joshua", "avatar_url": "/static/images/avatars/avatar_blue.svg"}
        }
        service = VlogCommentService(repository=self.repo, display_name_service=name_service)

        comments, total = service.get_comments("v1", "127.0.0.1", 1, 10)

        self.assertEqual(total, 1)
        self.assertEqual(comments[0]["author_name"], "Joshua")
        self.assertEqual(comments[0]["avatar_url"], "/static/images/avatars/avatar_blue.svg")
        self.assertTrue(comments[0]["is_own"])
        name_service.get_profiles_map.assert_called_once_with(["127.0.0.1"])

    def test_get_comments_keeps_generated_name_for_other_users(self):
        self.repo.find__paginate_comments_by_vlog.return_value = [comment_doc("vlog_id")]
        self.repo.count_comments_by_vlog.return_value = 1
        name_service = MagicMock()
        name_service.get_profiles_map.return_value = {}
        service = VlogCommentService(repository=self.repo, display_name_service=name_service)

        comments, total = service.get_comments("v1", "8.8.8.8", 1, 10)

        self.assertEqual(total, 1)
        self.assertEqual(comments[0]["author_name"], "user_abgzza")
        self.assertEqual(comments[0]["avatar_url"], "/static/images/user.webp")
        self.assertFalse(comments[0]["is_own"])

    def test_delete_comment_deletes_when_owner(self):
        self.repo.find_by_id.return_value = {"_id": VALID_OBJECT_ID, "ip_address": "127.0.0.1"}

        result = self.service.delete_comment("comment-1", "127.0.0.1, 10.0.0.1")

        self.assertTrue(result)
        self.repo.delete_by_id.assert_called_once_with("comment-1")

    def test_delete_comment_returns_none_when_missing(self):
        self.repo.find_by_id.return_value = None

        result = self.service.delete_comment("comment-1", "127.0.0.1")

        self.assertIsNone(result)
        self.repo.delete_by_id.assert_not_called()

    def test_delete_comment_rejects_other_users_comment(self):
        self.repo.find_by_id.return_value = {"_id": VALID_OBJECT_ID, "ip_address": "8.8.8.8"}

        result = self.service.delete_comment("comment-1", "127.0.0.1")

        self.assertFalse(result)
        self.repo.delete_by_id.assert_not_called()

    def test_delete_all_comments_delegates_to_repository(self):
        self.repo.delete_all_by_content_and_ip.return_value = 3

        result = self.service.delete_all_comments("v1", "127.0.0.1, 10.0.0.1")

        self.assertEqual(result, 3)
        self.repo.delete_all_by_content_and_ip.assert_called_once_with("vlog_id", "v1", "127.0.0.1")

    def test_get_profile_delegates_to_name_service(self):
        name_service = MagicMock()
        name_service.get_profile.return_value = ("Joshua", "/a.webp", 5)
        service = VlogCommentService(repository=self.repo, display_name_service=name_service)

        result = service.get_profile("127.0.0.1")

        self.assertEqual(result, ("Joshua", "/a.webp", 5))
        name_service.get_profile.assert_called_once_with("127.0.0.1")

    def test_get_profile_returns_defaults_without_service(self):
        result = self.service.get_profile("127.0.0.1")

        self.assertEqual(result, (None, "/static/images/user.webp", None))

    def test_get_display_name_delegates_to_name_service(self):
        name_service = MagicMock()
        name_service.get_display_name.return_value = ("Joshua", 4)
        service = VlogCommentService(repository=self.repo, display_name_service=name_service)

        result = service.get_display_name("127.0.0.1")

        self.assertEqual(result, ("Joshua", 4))
        name_service.get_display_name.assert_called_once_with("127.0.0.1")

    def test_get_display_name_returns_none_without_service(self):
        result = self.service.get_display_name("127.0.0.1")

        self.assertEqual(result, (None, None))

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
