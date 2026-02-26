import unittest
from unittest.mock import MagicMock

from backend.Services.LoginAttemptService import LoginAttemptService
from backend.configurations import SortOrder


class LoginAttemptServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = LoginAttemptService(repository=self.repo)

    def test_get_login_attempt_by_id_returns_repository_value(self):
        self.repo.get_login_attempt_by_id.return_value = {"_id": "127.0.0.1", "attempts": 1}

        result = self.service.get_login_attempt_by_id("127.0.0.1")

        self.assertEqual(result["attempts"], 1)
        self.repo.get_login_attempt_by_id.assert_called_once_with("127.0.0.1")

    def test_get_paginated_login_attempt_list_formats_lockout_time(self):
        self.repo.get_paginated_login_attempt_list.return_value = (
            [{"_id": "127.0.0.1", "attempts": 2, "lockout_until": "2026-01-01T00:00:00+00:00"}],
            1,
        )

        items, total = self.service.get_paginated_login_attempt_list(1, 10, SortOrder.DESC)

        self.assertEqual(total, 1)
        self.assertEqual(items[0].attempts, 2)
        self.assertIsInstance(items[0].lockout_until, str)
        self.assertIn("08:00 AM", items[0].lockout_until)

    def test_delete_login_attempt_returns_false_when_missing(self):
        self.repo.get_login_attempt_by_id.return_value = None

        result = self.service.delete_login_attempt("127.0.0.1")

        self.assertFalse(result)
        self.repo.delete_login_attempt.assert_not_called()

    def test_delete_login_attempt_deletes_when_found(self):
        self.repo.get_login_attempt_by_id.return_value = {"_id": "127.0.0.1", "attempts": 0}
        self.repo.delete_login_attempt.return_value = True

        result = self.service.delete_login_attempt("127.0.0.1")

        self.assertTrue(result)
        self.repo.delete_login_attempt.assert_called_once_with("127.0.0.1")


if __name__ == "__main__":
    unittest.main()
