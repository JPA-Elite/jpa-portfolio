import unittest
from unittest.mock import MagicMock, patch

from backend.Services.AuthService import AuthService
from backend.constants.messages import (
    PROFILE_UPDATE_MSG,
    UNAUTHORIZED_ACCESS_ERROR,
    USER_NOT_FOUND_ERROR,
)

from tests.services._service_fixtures import build_test_app


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        self.app = build_test_app()

    def test_update_profile_requires_session(self):
        service = AuthService(repository=MagicMock(), attempt_repository=MagicMock())
        with self.app.test_request_context("/admin/update-profile", json={"username": "admin"}):
            response, status = service.update_profile()

        self.assertEqual(status, 401)
        self.assertEqual(response.get_json()["message"], UNAUTHORIZED_ACCESS_ERROR)

    def test_update_profile_returns_not_found_when_user_missing(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        service = AuthService(repository=repo, attempt_repository=MagicMock())

        with self.app.test_request_context(
            "/admin/update-profile",
            json={"username": "admin-updated", "password": ""},
        ):
            from flask import session
            session["user_id"] = "user-1"
            response, status = service.update_profile()

        self.assertEqual(status, 404)
        self.assertEqual(response.get_json()["message"], USER_NOT_FOUND_ERROR)
        repo.update_user.assert_not_called()

    def test_update_profile_updates_username_without_hashing_when_password_blank(self):
        repo = MagicMock()
        repo.find_by_id.return_value = {"_id": "user-1", "username": "admin"}
        service = AuthService(repository=repo, attempt_repository=MagicMock())

        with self.app.test_request_context(
            "/admin/update-profile",
            json={"username": "new-admin", "password": "   "},
        ):
            from flask import session
            session["user_id"] = "user-1"
            response, status = service.update_profile()

        self.assertEqual(status, 200)
        self.assertEqual(response.get_json()["message"], PROFILE_UPDATE_MSG)
        repo.update_user.assert_called_once_with("user-1", {"username": "new-admin"})

    @patch("backend.Services.AuthService.generate_password_hash", return_value="hashed:newpass")
    def test_update_profile_hashes_password_when_provided(self, mock_generate_password_hash):
        repo = MagicMock()
        repo.find_by_id.return_value = {"_id": "user-1", "username": "admin"}
        service = AuthService(repository=repo, attempt_repository=MagicMock())

        with self.app.test_request_context(
            "/admin/update-profile",
            json={"username": "new-admin", "password": "newpass"},
        ):
            from flask import session
            session["user_id"] = "user-1"
            response, status = service.update_profile()

        self.assertEqual(status, 200)
        self.assertEqual(response.get_json()["message"], PROFILE_UPDATE_MSG)
        mock_generate_password_hash.assert_called_once_with("newpass")
        repo.update_user.assert_called_once_with(
            "user-1",
            {"username": "new-admin", "password": "hashed:newpass"},
        )


if __name__ == "__main__":
    unittest.main()
