import hashlib
import os
import smtplib
import ssl
import time
from email.message import EmailMessage
from datetime import datetime
from app.extensions import cache
from app.Repositories.Interfaces.IBookingRequestRepository import IBookingRequestRepository

class BookingService:
    RATE_LIMIT = 10
    RATE_WINDOW = 3600

    def __init__(self, repository: IBookingRequestRepository):
        self.smtp_host: str = os.getenv("SMTP_HOST", "")
        self.smtp_port: int = self._env_int("SMTP_PORT", 587)
        self.smtp_username: str = os.getenv("SMTP_USERNAME", "")
        self.smtp_password: str = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from: str = os.getenv("SMTP_FROM", self.smtp_username)
        self.smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "").strip()
        self.smtp_use_tls: bool = self._env_bool("SMTP_USE_TLS", True)
        self.smtp_use_ssl: bool = self._env_bool("SMTP_USE_SSL", False)
        self.repository = repository

    @staticmethod
    def _env_bool(name: str, default: bool):
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _env_int(name: str, default: int):
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    def _rate_limit_key(self, ip_hash: str):
        now = int(time.time())
        bucket = now // self.RATE_WINDOW
        return f"booking_rate:{ip_hash}:{bucket}"

    def check_rate_limit(self, ip_address: str):
        ip_hash = hashlib.sha256(ip_address.encode("utf-8")).hexdigest()[:24]
        key = self._rate_limit_key(ip_hash)
        count = cache.get(key) or 0

        if count >= self.RATE_LIMIT:
            now = int(time.time())
            retry_after = self.RATE_WINDOW - (now % self.RATE_WINDOW)
            return False, retry_after

        return True, 0

    def increment_count(self, ip_address: str):
        ip_hash = hashlib.sha256(ip_address.encode("utf-8")).hexdigest()[:24]
        key = self._rate_limit_key(ip_hash)
        count = (cache.get(key) or 0) + 1
        cache.set(key, count, timeout=self.RATE_WINDOW + 60)
        return count

    def save_booking(self, data: dict, ip_address: str):
        doc = {
            "name": data["name"],
            "email": data["email"],
            "preferred_date": data["preferred_date"],
            "preferred_time": data["preferred_time"],
            "message": data["message"],
            "service": data.get("service"),
            "ip_address": ip_address,
            "created_at": datetime.utcnow(),
            "read": False,
        }
        self.repository.insert_booking(doc)

    @staticmethod
    def _format_time_ampm(time_str: str) -> str:
        try:
            h, m = time_str.split(":")
            hour = int(h)
            ampm = "AM" if hour < 12 else "PM"
            hour12 = hour % 12
            if hour12 == 0:
                hour12 = 12
            return f"{hour12}:{m} {ampm}"
        except (ValueError, AttributeError):
            return time_str

    def send_booking_email(self, data: dict):
        to_email = self.smtp_username
        if not to_email:
            to_email = self.smtp_from

        subject = "New Booking Request - JPA Portfolio"

        time_display = self._format_time_ampm(data['preferred_time'])

        service_line = f"\nService: {data['service']}" if data.get('service') else ""

        body = (
            f"New Booking Request\n"
            f"{'─' * 40}\n"
            f"Name: {data['name']}\n"
            f"Email: {data['email']}\n"
            f"Date: {data['preferred_date']}\n"
            f"Time: {time_display}"
            f"{service_line}\n"
            f"Message: {data['message']}\n"
            f"{'─' * 40}\n"
            f"Sent via JPA Portfolio Booking System"
        )

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
