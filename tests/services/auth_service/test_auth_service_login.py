import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.Repositories.LoginAttemptRepository import MAX_ATTEMPTS
from app.Services.AuthService import AuthService
from app.constants.messages import (
    INVALID_USE_OR_PASS_ERROR,
    LOGIN_ATTEMPT_LOCKED_MSG,
    LOGIN_SUCCESS_MSG,
    MANY_FAILED_ATTEMPTS_ERROR,
)


class AuthServiceLoginTests(unittest.TestCase):
    def setUp(self):
        self.auth_repo = MagicMock()
        self.attempt_repo = MagicMock()
        self.service = AuthService(repository=self.auth_repo, attempt_repository=self.attempt_repo)

    def test_authenticate_admin_returns_lock_message_when_attempts_are_locked(self):
        self.attempt_repo.get_attempt_info.return_value = {
            "attempts": MAX_ATTEMPTS,
            "lockout_until": datetime.utcnow() + timedelta(minutes=10),
        }

        user, message, is_locked = self.service.authenticate_admin("admin", "secret")

        self.assertIsNone(user)
        self.assertTrue(is_locked)
        self.assertIn("Try again in", message)
        self.auth_repo.find_by_username.assert_not_called()
        self.attempt_repo.update_attempt.assert_not_called()

    @patch("app.Services.AuthService.check_password_hash", return_value=True)
    def test_authenticate_admin_ignores_expired_lockout_and_allows_login(self, _mock_check_password):
        self.attempt_repo.get_attempt_info.return_value = {
            "attempts": MAX_ATTEMPTS,
            "lockout_until": datetime.utcnow() - timedelta(minutes=1),
        }
        user_doc = {"_id": "u1", "username": "admin", "password": "hashed"}
        self.auth_repo.find_by_username.return_value = user_doc

        user, message, is_locked = self.service.authenticate_admin("admin", "correct-password")

        self.assertEqual(user, user_doc)
        self.assertEqual(message, LOGIN_SUCCESS_MSG)
        self.assertFalse(is_locked)
        self.auth_repo.find_by_username.assert_called_once_with("admin")
        self.attempt_repo.update_attempt.assert_called_once_with(success=True)

    def test_authenticate_admin_returns_remaining_attempts_for_unknown_user(self):
        self.attempt_repo.get_attempt_info.return_value = {"attempts": 1, "lockout_until": None}
        self.auth_repo.find_by_username.return_value = None

        user, message, is_locked = self.service.authenticate_admin("missing-user", "secret")

        self.assertIsNone(user)
        self.assertFalse(is_locked)
        self.assertEqual(message, INVALID_USE_OR_PASS_ERROR.format(attempts=1))
        self.attempt_repo.update_attempt.assert_called_once_with(success=False)

    @patch("app.Services.AuthService.check_password_hash", return_value=True)
    def test_authenticate_admin_success_resets_attempts(self, _mock_check_password):
        self.attempt_repo.get_attempt_info.return_value = {"attempts": 2, "lockout_until": None}
        user_doc = {"_id": "u1", "username": "admin", "password": "hashed"}
        self.auth_repo.find_by_username.return_value = user_doc

        user, message, is_locked = self.service.authenticate_admin("admin", "correct-password")

        self.assertEqual(user, user_doc)
        self.assertEqual(message, LOGIN_SUCCESS_MSG)
        self.assertFalse(is_locked)
        self.attempt_repo.update_attempt.assert_called_once_with(success=True)

    @patch("app.Services.AuthService.check_password_hash", return_value=False)
    def test_authenticate_admin_failed_password_locks_when_threshold_reached(self, _mock_check_password):
        self.attempt_repo.get_attempt_info.return_value = {"attempts": 2, "lockout_until": None}
        self.auth_repo.find_by_username.return_value = {"username": "admin", "password": "hashed"}
        self.attempt_repo.update_attempt.return_value = {
            "attempts": MAX_ATTEMPTS,
            "lockout_until": datetime.utcnow() + timedelta(hours=1),
        }

        user, message, is_locked = self.service.authenticate_admin("admin", "wrong-password")

        self.assertIsNone(user)
        self.assertEqual(message, MANY_FAILED_ATTEMPTS_ERROR)
        self.assertTrue(is_locked)
        self.attempt_repo.update_attempt.assert_called_once_with(success=False)

    @patch("app.Services.AuthService.check_password_hash", return_value=False)
    def test_authenticate_admin_failed_password_returns_remaining_attempts(self, _mock_check_password):
        self.attempt_repo.get_attempt_info.return_value = {"attempts": 0, "lockout_until": None}
        self.auth_repo.find_by_username.return_value = {"username": "admin", "password": "hashed"}
        self.attempt_repo.update_attempt.return_value = {"attempts": 1, "lockout_until": None}

        user, message, is_locked = self.service.authenticate_admin("admin", "wrong-password")

        self.assertIsNone(user)
        self.assertFalse(is_locked)
        self.assertEqual(message, INVALID_USE_OR_PASS_ERROR.format(attempts=2))
        self.assertNotEqual(message, LOGIN_ATTEMPT_LOCKED_MSG.format(minutes=0))


if __name__ == "__main__":
    unittest.main()
