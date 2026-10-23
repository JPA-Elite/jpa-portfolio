import importlib
import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

from app.Repositories.BaseRepository import BaseRepository


def _fake_get_mongo_client(self, collection_name):
    return object(), {}, MagicMock()


class ApiAdminOtpControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(BaseRepository, "get_mongo_client", new=_fake_get_mongo_client):
            cls.module = importlib.import_module(
                "app.Controllers.api.AdminOtpController"
            )

    def setUp(self):
        self.service = MagicMock()
        self.service_factory = MagicMock(return_value=self.service)
        self.service_patcher = patch.object(
            self.module, "OtpService", self.service_factory
        )
        self.service_patcher.start()
        self.addCleanup(self.service_patcher.stop)

        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"
        self.app.add_url_rule(
            "/admin/api/otp/send",
            endpoint="admin_otp_send",
            view_func=self.module.admin_otp_send_route,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/admin/api/otp/verify",
            endpoint="admin_otp_verify",
            view_func=self.module.admin_otp_verify_route,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/admin/api/otp/reset",
            endpoint="admin_otp_reset",
            view_func=self.module.admin_otp_reset_route,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/admin/api/otp/email",
            endpoint="admin_otp_email_get",
            view_func=self.module.admin_otp_email_get_route,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/admin/api/otp/email",
            endpoint="admin_otp_email_save",
            view_func=self.module.admin_otp_email_save_route,
            methods=["POST"],
        )
        self.client = self.app.test_client()

    def _login(self):
        with self.client.session_transaction() as session:
            session["user_id"] = "user-1"

    def _face_verified(self):
        with self.client.session_transaction() as session:
            return session.get("face_verified")

    def test_send_requires_authenticated_admin(self):
        response = self.client.post(
            "/admin/api/otp/send", json={"email": "admin@example.com"}
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.get_json(), {"ok": False, "message": "Not authenticated"}
        )
        self.service_factory.assert_not_called()

    def test_send_uses_supplied_email(self):
        self._login()
        self.service.send_otp.return_value = "OTP sent to your email."

        response = self.client.post(
            "/admin/api/otp/send", json={"email": " admin@example.com "}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"ok": True, "message": "OTP sent to your email."},
        )
        self.service.send_otp.assert_called_once_with(
            user_id="user-1", email="admin@example.com"
        )

    def test_send_resolves_configured_email_when_payload_is_empty(self):
        self._login()
        self.service.get_user_email.return_value = "configured@example.com"
        self.service.send_otp.return_value = "OTP sent to your email."

        response = self.client.post("/admin/api/otp/send", json={})

        self.assertEqual(response.status_code, 200)
        self.service.get_user_email.assert_called_once_with("user-1")
        self.service.send_otp.assert_called_once_with(
            user_id="user-1", email="configured@example.com"
        )

    def test_send_requires_configured_email(self):
        self._login()
        self.service.get_user_email.return_value = ""

        response = self.client.post("/admin/api/otp/send", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {
                "ok": False,
                "message": "OTP email not configured. Please set it in Admin Settings.",
            },
        )
        self.service.send_otp.assert_not_called()

    def test_send_handles_email_lookup_failure(self):
        self._login()
        self.service.get_user_email.side_effect = RuntimeError("lookup failed")

        response = self.client.post("/admin/api/otp/send", json={})

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["ok"])
        self.service.send_otp.assert_not_called()

    def test_send_returns_service_error(self):
        self._login()
        self.service.send_otp.side_effect = RuntimeError("SMTP down")

        response = self.client.post(
            "/admin/api/otp/send", json={"email": "admin@example.com"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(), {"ok": False, "message": "SMTP down"}
        )

    def test_verify_requires_otp(self):
        self._login()

        response = self.client.post("/admin/api/otp/verify", json={})

        self.assertEqual(response.status_code, 400)
        self.assertIn("otp", response.get_json()["errors"])
        self.service_factory.assert_not_called()

    def test_verify_requires_authenticated_admin(self):
        response = self.client.post(
            "/admin/api/otp/verify", json={"otp": "123456"}
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.get_json(), {"ok": False, "message": "Not authenticated"}
        )

    def test_verify_success_sets_session_gate(self):
        self._login()
        self.service.verify_otp.return_value = {
            "ok": True,
            "reason": "ok",
            "message": "OTP verified",
        }

        response = self.client.post(
            "/admin/api/otp/verify", json={"otp": " 123456 "}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(), {"ok": True, "message": "OTP verified"}
        )
        self.assertTrue(self._face_verified())
        self.service.verify_otp.assert_called_once_with(
            user_id="user-1", otp="123456"
        )

    def test_verify_invalid_code_returns_forbidden_with_attempts(self):
        self._login()
        self.service.verify_otp.return_value = {
            "ok": False,
            "reason": "invalid",
            "message": "Incorrect code.",
            "attempts_remaining": 3,
            "retry_after_seconds": None,
        }

        response = self.client.post(
            "/admin/api/otp/verify", json={"otp": "000000"}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.get_json(),
            {
                "ok": False,
                "message": "Incorrect code.",
                "reason": "invalid",
                "retry_after_seconds": None,
                "attempts_remaining": 3,
            },
        )
        self.assertIsNone(self._face_verified())

    def test_verify_cooldown_returns_too_many_requests(self):
        self._login()
        self.service.verify_otp.return_value = {
            "ok": False,
            "reason": "cooldown",
            "message": "Please wait.",
            "attempts_remaining": 0,
            "retry_after_seconds": 42,
        }

        response = self.client.post(
            "/admin/api/otp/verify", json={"otp": "000000"}
        )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.get_json()["retry_after_seconds"], 42)
        self.assertEqual(response.get_json()["reason"], "cooldown")

    def test_reset_clears_session_gate(self):
        self._login()
        with self.client.session_transaction() as session:
            session["face_verified"] = True

        response = self.client.post("/admin/api/otp/reset", json={})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"ok": True, "message": "OTP verification gate cleared"},
        )
        self.assertIsNone(self._face_verified())

    def test_email_get_requires_authenticated_admin(self):
        response = self.client.get("/admin/api/otp/email")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.get_json(), {"ok": False, "message": "Not authenticated"}
        )

    def test_email_get_returns_email_without_cooldown(self):
        self._login()
        self.service.get_user_email.return_value = "admin@example.com"
        self.service.get_cooldown_remaining_seconds.return_value = 0

        response = self.client.get("/admin/api/otp/email")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "ok": True,
                "email": "admin@example.com",
                "retry_after_seconds": 0,
                "message": "",
            },
        )
        self.service.get_user_email.assert_called_once_with("user-1")
        self.service.get_cooldown_remaining_seconds.assert_called_once_with("user-1")

    def test_email_get_returns_cooldown_message(self):
        self._login()
        self.service.get_user_email.return_value = "admin@example.com"
        self.service.get_cooldown_remaining_seconds.return_value = 45

        response = self.client.get("/admin/api/otp/email")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["retry_after_seconds"], 45)
        self.assertIn("45 seconds", response.get_json()["message"])

    def test_email_save_requires_email(self):
        self._login()

        response = self.client.post("/admin/api/otp/email", json={"email": ""})

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.get_json()["errors"])
        self.service_factory.assert_not_called()

    def test_email_save_updates_configured_email(self):
        self._login()

        response = self.client.post(
            "/admin/api/otp/email", json={"email": " new@example.com "}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"ok": True, "message": "OTP email updated"},
        )
        self.service.update_user_email.assert_called_once_with(
            "user-1", "new@example.com"
        )

    def test_email_save_requires_authenticated_admin(self):
        response = self.client.post(
            "/admin/api/otp/email", json={"email": "admin@example.com"}
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.get_json(), {"ok": False, "message": "Not authenticated"}
        )


if __name__ == "__main__":
    unittest.main()
