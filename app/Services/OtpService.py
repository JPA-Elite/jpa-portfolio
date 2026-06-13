import os
import random
import smtplib
import ssl
import time
from email.message import EmailMessage
from app.extensions import cache
from app.Repositories.AuthRepository import AuthRepository

class OtpService:
    _FIELD_ATTEMPTS = "admin_otp_attempts"
    _FIELD_COOLDOWN_UNTIL = "admin_otp_cooldown_until"

    def __init__(self) -> None:
        self.otp_ttl_seconds: int = self._env_int("ADMIN_OTP_TTL_SECONDS", 300)
        self.otp_length: int = self._env_int("ADMIN_OTP_LENGTH", 6)

        self.smtp_host: str = os.getenv("SMTP_HOST", "")
        self.smtp_port: int = self._env_int("SMTP_PORT", 587)
        self.smtp_username: str = os.getenv("SMTP_USERNAME", "")
        self.smtp_password: str = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from: str = os.getenv("SMTP_FROM", self.smtp_username)
        self.smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "").strip()

        self.smtp_use_tls: bool = self._env_bool("SMTP_USE_TLS", True)
        self.smtp_use_ssl: bool = self._env_bool("SMTP_USE_SSL", False)

        self.otp_cooldown_seconds: int = self._env_int("ADMIN_OTP_COOLDOWN_SECONDS", 60)
        self.otp_max_attempts: int = self._env_int("ADMIN_OTP_MAX_ATTEMPTS", 5)

    @staticmethod
    def _env_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _env_int(name: str, default: int) -> int:
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    def _otp_key(self, user_id: str) -> str:
        return f"admin_otp:{user_id}"

    def _now(self) -> float:
        return time.time()

    def _generate_otp(self) -> str:
        upper = 10 ** self.otp_length
        otp = random.randint(0, upper - 1)
        return str(otp).zfill(self.otp_length)

    def _get_user_otp_state(self, user_id: str) -> tuple[int, float]:
        user_doc = AuthRepository().find_by_id(str(user_id)) or {}
        attempts_raw = user_doc.get(self._FIELD_ATTEMPTS, 0)
        cooldown_until_raw = user_doc.get(self._FIELD_COOLDOWN_UNTIL, 0)

        try:
            attempts_int = int(attempts_raw)
        except (TypeError, ValueError):
            attempts_int = 0

        try:
            cooldown_until = float(cooldown_until_raw)
        except (TypeError, ValueError):
            cooldown_until = 0.0

        return attempts_int, cooldown_until

    def _set_user_otp_state(self, user_id: str, attempts: int, cooldown_until: float) -> None:
        AuthRepository().update_user(
            str(user_id),
            {
                self._FIELD_ATTEMPTS: int(attempts),
                self._FIELD_COOLDOWN_UNTIL: float(cooldown_until),
            },
        )

    def get_cooldown_remaining_seconds(self, user_id: str) -> int:
        attempts, cooldown_until = self._get_user_otp_state(user_id)
        now = self._now()
        if cooldown_until > now:
            return max(0, int(round(cooldown_until - now)))
        return 0

    def send_otp(self, user_id: str, email: str) -> str:
        if not user_id:
            raise ValueError("Missing user_id")
        email = (email or "").strip()
        if not email:
            raise ValueError("Missing email")

        if not (self.smtp_host and self.smtp_username and self.smtp_password and self.smtp_from):
            raise RuntimeError(
                "SMTP is not configured. Please set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM."
            )

        AuthRepository().update_user(user_id, {"email": email})

        otp = self._generate_otp()
        cache.set(self._otp_key(user_id), otp, timeout=self.otp_ttl_seconds)

        self._set_user_otp_state(user_id, attempts=0, cooldown_until=0.0)

        subject = "Your JPA-Admin verification code"
        body = (
            f"Your one-time verification code is: {otp}\n\n"
            f"This code will expire in {self.otp_ttl_seconds // 60} minute(s).\n"
            f"If you did not request this, you can ignore this email."
        )

        self._send_email_smtp(to_email=email, subject=subject, body=body)
        return "OTP sent to your email."

    def verify_otp(self, user_id: str, otp: str) -> dict:
        if not user_id:
            return {
                "ok": False,
                "reason": "invalid",
                "message": "Not authenticated.",
                "attempts_remaining": None,
                "retry_after_seconds": None,
            }

        otp = (otp or "").strip()
        if not otp:
            return {
                "ok": False,
                "reason": "invalid",
                "message": "Missing OTP.",
                "attempts_remaining": None,
                "retry_after_seconds": None,
            }

        attempts, cooldown_until = self._get_user_otp_state(user_id)
        now = self._now()

        if cooldown_until > now:
            retry_after = max(0, int(round(cooldown_until - now)))
            return {
                "ok": False,
                "reason": "cooldown",
                "message": f"Too many invalid attempts. Please wait {retry_after} seconds and try again.",
                "attempts_remaining": 0,
                "retry_after_seconds": retry_after,
            }

        key = self._otp_key(user_id)
        expected = cache.get(key)

        if expected is None:
            return self._handle_invalid_attempt(user_id, attempts)

        if str(expected) != otp:
            return self._handle_invalid_attempt(user_id, attempts)

        cache.delete(key)
        self._set_user_otp_state(user_id, attempts=0, cooldown_until=0.0)

        return {
            "ok": True,
            "reason": "ok",
            "message": "OTP verified",
            "attempts_remaining": None,
            "retry_after_seconds": None,
        }

    def _handle_invalid_attempt(self, user_id: str, attempts: int) -> dict:
        attempts = attempts + 1
        attempts_remaining = max(0, self.otp_max_attempts - attempts)
        now = self._now()

        if attempts >= self.otp_max_attempts:
            cooldown_until_new = now + self.otp_cooldown_seconds
            self._set_user_otp_state(user_id, attempts=0, cooldown_until=cooldown_until_new)

            return {
                "ok": False,
                "reason": "invalid",
                "message": f"Too many invalid attempts. Please wait {self.otp_cooldown_seconds} seconds and try again.",
                "attempts_remaining": 0,
                "retry_after_seconds": self.otp_cooldown_seconds,
            }

        self._set_user_otp_state(user_id, attempts=attempts, cooldown_until=0.0)

        return {
            "ok": False,
            "reason": "expired",
            "message": f"OTP expired or invalid. Attempts remaining: {attempts_remaining}.",
            "attempts_remaining": attempts_remaining,
            "retry_after_seconds": None,
        }

    def _send_email_smtp(self, to_email: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        if self.smtp_from_name:
            msg["From"] = f"{self.smtp_from_name} <{self.smtp_from}>"
        else:
            msg["From"] = self.smtp_from
        msg["To"] = to_email
        msg.set_content(body)

        if self.smtp_use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            return

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
            if self.smtp_use_tls:
                server.starttls(context=ssl.create_default_context())
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)

