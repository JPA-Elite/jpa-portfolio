import os
import unittest
from unittest.mock import patch

from app.Services.OtpService import OtpService


class FakeAuthRepository:
    store = {}

    def __init__(self, *args, **kwargs):
        pass

    def find_by_id(self, user_id):
        return dict(FakeAuthRepository.store.get(str(user_id), {}))

    def update_user(self, user_id, data):
        doc = FakeAuthRepository.store.setdefault(str(user_id), {})
        doc.update(data)
        return True


class OtpServiceTests(unittest.TestCase):
    def setUp(self):
        FakeAuthRepository.store = {}
        env = {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "admin@example.com",
            "SMTP_PASSWORD": "secret",
            "SMTP_FROM": "admin@example.com",
            "ADMIN_OTP_TTL_SECONDS": "300",
            "ADMIN_OTP_LENGTH": "6",
            "ADMIN_OTP_MAX_ATTEMPTS": "5",
            "ADMIN_OTP_COOLDOWN_SECONDS": "60",
        }
        self._env_patcher = patch.dict(os.environ, env)
        self._env_patcher.start()
        self.addCleanup(self._env_patcher.stop)
        self._repo_patcher = patch("app.Services.OtpService.AuthRepository", FakeAuthRepository)
        self._repo_patcher.start()
        self.addCleanup(self._repo_patcher.stop)
        self._mail_patcher = patch.object(OtpService, "_send_email_smtp", return_value=None)
        self._mail_patcher.start()
        self.addCleanup(self._mail_patcher.stop)

    def _send_code(self, user_id="user-1"):
        sender = OtpService()
        sender.send_otp(user_id, "admin@example.com")
        return FakeAuthRepository.store[user_id]["admin_otp_code"]

    def test_send_then_verify_with_fresh_instance_succeeds(self):
        code = self._send_code()
        verifier = OtpService()
        result = verifier.verify_otp("user-1", code)
        self.assertTrue(result["ok"])
        self.assertEqual(result["reason"], "ok")

    def test_code_is_single_use(self):
        code = self._send_code()
        verifier = OtpService()
        self.assertTrue(verifier.verify_otp("user-1", code)["ok"])
        second = OtpService().verify_otp("user-1", code)
        self.assertFalse(second["ok"])
        self.assertEqual(second["reason"], "expired")

    def test_wrong_code_reports_invalid_with_attempts_remaining(self):
        self._send_code()
        result = OtpService().verify_otp("user-1", "000000")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "invalid")
        self.assertEqual(result["attempts_remaining"], 4)

    def test_expired_code_reports_expired(self):
        self._send_code()
        FakeAuthRepository.store["user-1"]["admin_otp_expires_at"] = 0.0
        result = OtpService().verify_otp("user-1", FakeAuthRepository.store["user-1"]["admin_otp_code"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "expired")

    def test_missing_code_reports_expired(self):
        result = OtpService().verify_otp("ghost-user", "123456")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "expired")

    def test_max_attempts_triggers_cooldown(self):
        self._send_code()
        service = OtpService()
        for _ in range(5):
            result = service.verify_otp("user-1", "000000")
        self.assertEqual(result["reason"], "invalid")
        self.assertEqual(result["attempts_remaining"], 0)
        locked = OtpService().verify_otp("user-1", "000000")
        self.assertEqual(locked["reason"], "cooldown")
        self.assertIsNotNone(locked["retry_after_seconds"])


if __name__ == "__main__":
    unittest.main()
