from datetime import datetime, timedelta
import os
import tempfile
import secrets
import smtplib
import re
from typing import Optional
from email.message import EmailMessage
import requests

from werkzeug.security import check_password_hash, generate_password_hash

from backend.Repositories.ServerUserRepository import ServerUserRepository
from backend.Repositories.ServerChannelRepository import ServerChannelRepository
from backend.Repositories.ServerMessageRepository import ServerMessageRepository
from backend.Repositories.ServerFileRepository import ServerFileRepository
from backend.configurations import SortOrder
from backend.constants.cloudinary import CloudinaryFolders, CloudinaryResourceType
from backend.utils import cleanup_uploaded_files, convert_to_webp, upload_file_to_cloudinary


class ServerCommunityService:
    DEFAULT_ADMIN_USERNAME = "serveradmin"
    DEFAULT_ADMIN_EMAIL = "serveradmin@example.com"
    DEFAULT_ADMIN_PASSWORD = "admin12345"
    DEFAULT_CHANNEL_SLUGS = {"general", "business-concerns"}
    OTP_EXPIRY_MINUTES = 10
    ONLINE_WINDOW_SECONDS = 120
    MEMBER_FILE_SIZE_LIMIT_BYTES = 1 * 1024 * 1024
    MEMBER_CHANNEL_FILE_LIMIT = 100
    CHAT_PAGE_LIMIT = 50
    THREAD_PAGE_LIMIT = 50
    MENTION_PATTERN = re.compile(r"(?<![\\w])@([a-zA-Z0-9._-]{2,32})")
    ALLOWED_REACTIONS = {
        "👍",
        "👎",
        "❤️",
        "🔥",
        "👏",
        "✅",
        "🎉",
        "😂",
        "😍",
        "🤔",
        "🙏",
        "🚀",
        "💡",
        "🎯",
        "🤝",
        "😢",
        "🥳",
        "👌",
        "🌟",
        "💯",
        "😎",
        "🙌",
        "😮",
        "😡",
    }

    def __init__(
        self,
        user_repository: ServerUserRepository,
        channel_repository: ServerChannelRepository,
        message_repository: ServerMessageRepository,
        file_repository: Optional[ServerFileRepository] = None,
    ):
        self.user_repository = user_repository
        self.channel_repository = channel_repository
        self.message_repository = message_repository
        self.file_repository = file_repository or ServerFileRepository()

    def seed_defaults(self):
        self.channel_repository.ensure_default_channels()
        self._ensure_default_admin_account()

    def _ensure_default_admin_account(self):
        if self.user_repository.count_admin_accounts() > 0:
            return

        self.user_repository.add_user(
            {
                "name": "Server Admin",
                "username": self.DEFAULT_ADMIN_USERNAME,
                "username_lower": self.DEFAULT_ADMIN_USERNAME.lower(),
                "email": self.DEFAULT_ADMIN_EMAIL,
                "email_lower": self.DEFAULT_ADMIN_EMAIL.lower(),
                "password": generate_password_hash(self.DEFAULT_ADMIN_PASSWORD),
                "birthdate": "",
                "place": "",
                "gender": "",
                "profile_image": "/static/admin/assets/img/admin.png",
                "account_type": "admin",
                "is_active": True,
                "is_online": False,
                "last_active_at": None,
            }
        )

    def register_account(self, data: dict):
        name = str(data.get("name") or "").strip()
        username = str(data.get("username") or "").strip()
        email = str(data.get("email") or "").strip()
        password = str(data.get("password") or "").strip()
        birthdate = str(data.get("birthdate") or "").strip()
        place = str(data.get("place") or "").strip()
        gender = str(data.get("gender") or "").strip()

        if not all([name, username, email, password, birthdate, place, gender]):
            raise ValueError("All required fields must be filled.")

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")

        if self.user_repository.find_by_username(username):
            raise ValueError("Username is already taken.")
        if self.user_repository.find_by_email(email):
            raise ValueError("Email is already registered.")

        user_id = self.user_repository.add_user(
            {
                "name": name,
                "username": username,
                "username_lower": username.lower(),
                "email": email,
                "email_lower": email.lower(),
                "password": generate_password_hash(password),
                "birthdate": birthdate,
                "place": place,
                "gender": gender,
                "profile_image": "/static/admin/assets/img/admin.png",
                "account_type": "member",
                "is_active": True,
                "is_online": False,
                "last_active_at": None,
            }
        )
        user = self.user_repository.get_user_by_id(user_id)
        self.ensure_private_business_channel_for_user(user)
        return self.serialize_user(user)

    def authenticate(self, login_value: str, password: str):
        user = self.user_repository.find_by_login(login_value)
        if not user:
            return None, "Invalid username/email or password."

        if user.get("is_active") is False:
            return None, "This account is inactive."

        if not check_password_hash(user.get("password", ""), password or ""):
            return None, "Invalid username/email or password."

        self.user_repository.touch_last_active(str(user.get("_id")))
        self.channel_repository.ensure_default_channels()
        self.ensure_private_business_channel_for_user(user)
        return self.serialize_user(self.user_repository.get_user_by_id(str(user.get("_id")))), None

    def authenticate_with_google(self, id_token: str, mode: str = "login"):
        google_user = self._verify_firebase_id_token(id_token)
        email = str(google_user.get("email") or "").strip()
        if not email:
            raise ValueError("Google account email is required.")

        normalized_mode = str(mode or "login").strip().lower()
        if normalized_mode not in {"login", "register", "auto"}:
            normalized_mode = "login"

        user = self.user_repository.find_by_email(email)
        if normalized_mode == "register" and user:
            raise ValueError("Email is already registered. Please sign in.")
        if normalized_mode == "login" and not user:
            raise ValueError("No account found for this Google email. Please sign up first.")

        if not user:
            user = self._create_google_user(google_user)
        elif user.get("is_active") is False:
            raise ValueError("This account is inactive.")
        else:
            self._sync_existing_google_user(user, google_user)
            user = self.user_repository.get_user_by_id(str(user.get("_id")))

        self.user_repository.touch_last_active(str(user.get("_id")))
        self.channel_repository.ensure_default_channels()
        self.ensure_private_business_channel_for_user(user)
        return self.serialize_user(self.user_repository.get_user_by_id(str(user.get("_id"))))

    def request_password_reset_otp(self, login_value: str):
        login_value = str(login_value or "").strip()
        if not login_value:
            raise ValueError("Username/email is required.")

        user = self.user_repository.find_by_login(login_value)
        if not user:
            return {
                "masked_email": "",
                "message": "Failure to send OTP, the account does not exist.",
            }

        email = str(user.get("email") or "").strip()
        if not email:
            raise ValueError("This account has no email configured.")

        otp_code = f"{secrets.randbelow(1_000_000):06d}"
        subject = "Server Community Password Reset OTP"
        body = (
            "Your OTP code is: "
            f"{otp_code}\n\n"
            f"This code expires in {self.OTP_EXPIRY_MINUTES} minutes."
        )
        html_body = self._build_otp_email_html(
            recipient_name=str(user.get("name") or user.get("username") or "Member"),
            otp_code=otp_code,
            expiry_minutes=self.OTP_EXPIRY_MINUTES,
        )
        self._send_smtp_email(email, subject, body, html_body=html_body)

        self.user_repository.update_user(
            str(user.get("_id")),
            {
                "password_reset_otp_hash": generate_password_hash(otp_code),
                "password_reset_otp_expires_at": datetime.utcnow() + timedelta(minutes=self.OTP_EXPIRY_MINUTES),
                "password_reset_requested_at": datetime.utcnow(),
            },
        )
        return {
            "masked_email": self._mask_email(email),
            "message": "Failure to send OTP, the account does not exist.",
        }

    def reset_password_with_otp(self, login_value: str, otp_code: str, new_password: str):
        login_value = str(login_value or "").strip()
        otp_code = str(otp_code or "").strip()
        new_password = str(new_password or "").strip()

        if not login_value:
            raise ValueError("Username/email is required.")
        if not otp_code:
            raise ValueError("OTP code is required.")
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters.")

        user = self.user_repository.find_by_login(login_value)
        if not user:
            raise ValueError("Invalid account or OTP.")

        otp_hash = str(user.get("password_reset_otp_hash") or "").strip()
        otp_expires_at = user.get("password_reset_otp_expires_at")
        if not otp_hash or not otp_expires_at:
            raise ValueError("No active OTP found. Request a new OTP.")
        if isinstance(otp_expires_at, datetime) and otp_expires_at < datetime.utcnow():
            raise ValueError("OTP has expired. Request a new OTP.")
        if not check_password_hash(otp_hash, otp_code):
            raise ValueError("Invalid OTP code.")

        self.user_repository.update_user(
            str(user.get("_id")),
            {
                "password": generate_password_hash(new_password),
                "password_reset_otp_hash": "",
                "password_reset_otp_expires_at": None,
                "password_reset_requested_at": None,
            },
        )

    def set_user_online_status(self, user_id: str, is_online: bool):
        user_id = str(user_id or "").strip()
        if not user_id:
            return False
        return self.user_repository.set_online_status(user_id, is_online)

    def touch_user_activity(self, user_id: str):
        user_id = str(user_id or "").strip()
        if not user_id:
            return False
        return self.user_repository.touch_last_active(user_id)

    def get_user_by_id(self, user_id: str):
        user = self.user_repository.get_user_by_id(user_id)
        return self.serialize_user(user) if user else None

    def get_user_document_by_id(self, user_id: str):
        return self.user_repository.get_user_by_id(user_id)

    def update_profile(self, user_id: str, data: dict, profile_image_file=None):
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        update_data = {}
        for key in ("name", "birthdate", "place", "gender"):
            if key in data:
                value = str(data.get(key) or "").strip()
                if value:
                    update_data[key] = value

        username = str(data.get("username") or "").strip()
        if username and username.lower() != str(user.get("username_lower") or "").lower():
            if self.user_repository.find_by_username(username):
                raise ValueError("Username is already taken.")
            update_data["username"] = username
            update_data["username_lower"] = username.lower()

        email = str(data.get("email") or "").strip()
        if email and email.lower() != str(user.get("email_lower") or "").lower():
            if self.user_repository.find_by_email(email):
                raise ValueError("Email is already registered.")
            update_data["email"] = email
            update_data["email_lower"] = email.lower()

        password = str(data.get("password") or "").strip()
        if password:
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters.")
            update_data["password"] = generate_password_hash(password)

        uploaded_image_url = None
        previous_image = user.get("profile_image")
        if profile_image_file:
            uploaded_image_url = self._upload_profile_image(profile_image_file)
            update_data["profile_image"] = uploaded_image_url

        if update_data:
            self.user_repository.update_user(user_id, update_data)

        if (
            uploaded_image_url
            and previous_image
            and "res.cloudinary.com" in str(previous_image)
            and previous_image != uploaded_image_url
        ):
            cleanup_uploaded_files(None, previous_image)

        updated = self.user_repository.get_user_by_id(user_id)
        return self.serialize_user(updated)

    def ensure_private_business_channel_for_user(self, user_document: dict):
        if not user_document:
            return None

        user_id = str(user_document.get("_id"))
        existing = self.channel_repository.get_channel_by_user(user_id)
        if existing:
            return existing

        username = str(user_document.get("username") or "member").strip()
        base_slug = self.channel_repository.slugify(f"business-{username}")
        slug = f"{base_slug}-{user_id[:6]}"
        suffix = 1
        while self.channel_repository.get_channel_by_slug(slug):
            suffix += 1
            slug = f"{base_slug}-{user_id[:6]}-{suffix}"

        member_ids = [user_id]
        for admin_id in self.user_repository.get_server_admin_user_ids():
            if admin_id not in member_ids:
                member_ids.append(admin_id)

        channel_id = self.channel_repository.add_channel(
            {
                "name": f"business-{username}",
                "slug": slug,
                "description": f"Private business concerns channel for {username}.",
                "channel_type": "concern",
                "is_public": False,
                "owner_user_id": user_id,
                "member_ids": member_ids,
            }
        )
        return self.channel_repository.get_channel_by_id(channel_id)

    def list_channels_for_user(self, user_document: dict):
        if not user_document:
            return []

        self.channel_repository.ensure_default_channels()
        self.ensure_private_business_channel_for_user(user_document)
        channels = self.channel_repository.list_channels_for_user(
            str(user_document.get("_id")),
            str(user_document.get("account_type") or "member"),
        )
        channel_file_counts = self.file_repository.count_files_for_channels(
            [str(item.get("_id")) for item in channels if item.get("_id")]
        )

        active_users = self.user_repository.list_active_users()
        user_lookup = {}
        for row in active_users:
            user_id = str(row.get("_id") or "").strip()
            if not user_id:
                continue
            user_lookup[user_id] = row

        sorted_user_ids = sorted(
            user_lookup.keys(),
            key=lambda user_id: (
                0 if self._is_user_online(user_lookup.get(user_id)) else 1,
                str(user_lookup.get(user_id, {}).get("username") or "").lower(),
            ),
        )

        payload = []
        current_user_id = str(user_document.get("_id") or "").strip()
        is_admin = str(user_document.get("account_type") or "").strip().lower() == "admin"
        for item in channels:
            serialized = self.serialize_channel(item)
            member_ids = [str(value) for value in (item.get("member_ids") or []) if str(value).strip()]
            if item.get("is_public"):
                channel_member_ids = list(sorted_user_ids)
            else:
                channel_member_ids = [value for value in member_ids if value in user_lookup]

            if current_user_id and current_user_id not in channel_member_ids:
                channel_member_ids.append(current_user_id)

            member_preview = []
            for member_id in channel_member_ids[:6]:
                user_row = user_lookup.get(member_id)
                if not user_row:
                    continue
                member_preview.append(
                    {
                        "id": member_id,
                        "username": str(user_row.get("username") or "member"),
                        "profile_image": str(
                            user_row.get("profile_image") or "/static/admin/assets/img/admin.png"
                        ),
                        "is_online": self._is_user_online(user_row),
                    }
                )

            serialized["member_count"] = len(channel_member_ids)
            serialized["member_preview"] = member_preview
            serialized["can_manage"] = self._can_manage_channel(user_document, item)
            serialized["is_default"] = str(item.get("slug") or "") in self.DEFAULT_CHANNEL_SLUGS
            serialized["file_count"] = int(channel_file_counts.get(serialized["id"], 0))
            serialized["file_limit"] = None if is_admin else self.MEMBER_CHANNEL_FILE_LIMIT
            payload.append(serialized)
        return payload

    @staticmethod
    def _normalize_pagination(page: int, per_page: int, default_per_page: int = 100):
        safe_page = max(1, int(page or 1))
        safe_per_page = max(1, min(int(per_page or default_per_page), 500))
        return safe_page, safe_per_page

    def get_messages_for_channel(
        self,
        user_document: dict,
        channel_id: str,
        *,
        page: int = 1,
        per_page: int = 100,
        search_query: str = "",
        pinned_only: bool = False,
    ):
        channel = self._validate_channel_access(user_document, channel_id)
        safe_page, safe_per_page = self._normalize_pagination(page, per_page)
        safe_per_page = min(safe_per_page, self.CHAT_PAGE_LIMIT)
        normalized_search = str(search_query or "").strip()
        include_root_ids = []
        if normalized_search:
            include_root_ids = self.message_repository.find_parent_ids_for_reply_search(
                str(channel.get("_id")),
                normalized_search,
            )

        root_rows, total = self.message_repository.get_messages_page(
            str(channel.get("_id")),
            page=safe_page,
            per_page=safe_per_page,
            scope="root",
            search_query=normalized_search,
            pinned_only=bool(pinned_only),
            include_ids=include_root_ids,
            sort_desc=True,
        )
        ordered_rows = list(reversed(root_rows))
        root_ids = [str(item.get("_id")) for item in ordered_rows if item.get("_id")]
        reply_stats = self.message_repository.get_reply_stats_for_parents(
            str(channel.get("_id")),
            root_ids,
        )

        current_user_id = str(user_document.get("_id"))
        current_account_type = str(user_document.get("account_type") or "member")
        serialized_rows = []
        for item in ordered_rows:
            serialized = self.serialize_message(
                item,
                current_user_id=current_user_id,
                current_account_type=current_account_type,
            )
            stats = reply_stats.get(serialized["id"], {})
            last_reply_at = stats.get("last_reply_at")
            serialized["reply_count"] = int(stats.get("reply_count") or 0)
            serialized["last_reply_at"] = (
                last_reply_at.isoformat() + "Z" if last_reply_at else None
            )
            serialized_rows.append(serialized)

        total_pages = (total + safe_per_page - 1) // safe_per_page if total > 0 else 1
        return {
            "messages": serialized_rows,
            "pagination": {
                "page": safe_page,
                "per_page": safe_per_page,
                "total_items": total,
                "total_pages": total_pages,
            },
        }

    def get_thread_messages_for_channel(
        self,
        user_document: dict,
        channel_id: str,
        parent_message_id: str,
        *,
        page: int = 1,
        per_page: int = 100,
        search_query: str = "",
    ):
        channel = self._validate_channel_access(user_document, channel_id)
        root_message = self.message_repository.get_message_by_id(parent_message_id)
        if not root_message:
            raise ValueError("Thread root message not found.")
        if str(root_message.get("channel_id") or "") != str(channel.get("_id")):
            raise PermissionError("Thread message does not belong to this channel.")

        safe_page, safe_per_page = self._normalize_pagination(page, per_page)
        safe_per_page = min(safe_per_page, self.THREAD_PAGE_LIMIT)
        replies, total = self.message_repository.get_messages_page(
            str(channel.get("_id")),
            page=safe_page,
            per_page=safe_per_page,
            scope="thread",
            parent_message_id=str(parent_message_id or "").strip(),
            search_query=str(search_query or "").strip(),
            sort_desc=True,
        )
        current_user_id = str(user_document.get("_id"))
        current_account_type = str(user_document.get("account_type") or "member")
        serialized_replies = [
            self.serialize_message(
                item,
                current_user_id=current_user_id,
                current_account_type=current_account_type,
            )
            for item in reversed(replies)
        ]
        total_pages = (total + safe_per_page - 1) // safe_per_page if total > 0 else 1
        return {
            "root_message": self.serialize_message(
                root_message,
                current_user_id=current_user_id,
                current_account_type=current_account_type,
            ),
            "replies": serialized_replies,
            "pagination": {
                "page": safe_page,
                "per_page": safe_per_page,
                "total_items": total,
                "total_pages": total_pages,
            },
        }

    def get_channel_activity(
        self,
        user_document: dict,
        channel_id: str,
        *,
        page: int = 1,
        per_page: int = 20,
        search_query: str = "",
    ):
        channel = self._validate_channel_access(user_document, channel_id)
        safe_page, safe_per_page = self._normalize_pagination(page, per_page, default_per_page=20)
        rows, total = self.message_repository.get_messages_page(
            str(channel.get("_id")),
            page=safe_page,
            per_page=safe_per_page,
            scope="all",
            search_query=str(search_query or "").strip(),
            sort_desc=True,
        )
        current_user_id = str(user_document.get("_id"))
        current_account_type = str(user_document.get("account_type") or "member")
        serialized_rows = [
            self.serialize_message(
                item,
                current_user_id=current_user_id,
                current_account_type=current_account_type,
            )
            for item in rows
        ]
        total_pages = (total + safe_per_page - 1) // safe_per_page if total > 0 else 1
        return {
            "messages": serialized_rows,
            "pagination": {
                "page": safe_page,
                "per_page": safe_per_page,
                "total_items": total,
                "total_pages": total_pages,
            },
        }

    def get_user_activity_feed(
        self,
        user_document: dict,
        *,
        page: int = 1,
        per_page: int = 20,
        filter_type: str = "all",
    ):
        if not user_document:
            return {"activities": [], "pagination": {"page": 1, "per_page": per_page, "total_items": 0, "total_pages": 1}}

        safe_page, safe_per_page = self._normalize_pagination(page, per_page, default_per_page=20)
        channels = self.channel_repository.list_channels_for_user(
            str(user_document.get("_id")),
            str(user_document.get("account_type") or "member"),
        )
        channel_map = {str(item.get("_id")): item for item in channels if item.get("_id")}
        if not channel_map:
            return {
                "activities": [],
                "pagination": {
                    "page": safe_page,
                    "per_page": safe_per_page,
                    "total_items": 0,
                    "total_pages": 1,
                },
            }

        rows, total = self.message_repository.get_messages_for_channels(
            list(channel_map.keys()),
            page=safe_page,
            per_page=safe_per_page,
            filter_type=filter_type,
            current_user_id=str(user_document.get("_id") or ""),
            current_username=str(user_document.get("username") or ""),
            sort_desc=True,
        )
        current_user_id = str(user_document.get("_id"))
        current_account_type = str(user_document.get("account_type") or "member")
        activities = []
        for row in rows:
            serialized = self.serialize_message(
                row,
                current_user_id=current_user_id,
                current_account_type=current_account_type,
            )
            channel_id = str(row.get("channel_id") or "")
            channel_row = channel_map.get(channel_id) or {}
            serialized["channel_id"] = channel_id
            serialized["channel_name"] = str(channel_row.get("name") or "channel")
            if self._is_message_mentioning_user(row, current_user_id, str(user_document.get("username") or "")):
                serialized["activity_kind"] = "mention"
            elif str(row.get("parent_message_id") or "").strip():
                serialized["activity_kind"] = "thread"
            elif current_user_id in [str(value) for value in (row.get("reaction_user_ids") or [])]:
                serialized["activity_kind"] = "reaction"
            else:
                serialized["activity_kind"] = "all"
            activities.append(serialized)

        total_pages = (total + safe_per_page - 1) // safe_per_page if total > 0 else 1
        return {
            "activities": activities,
            "pagination": {
                "page": safe_page,
                "per_page": safe_per_page,
                "total_items": total,
                "total_pages": total_pages,
            },
        }

    def send_message(self, user_document: dict, channel_id: str, text: str, parent_message_id: str = ""):
        text = str(text or "").strip()
        if not text:
            raise ValueError("Message text is required.")
        if len(text) > 3000:
            raise ValueError("Message text is too long.")

        channel = self._validate_channel_access(user_document, channel_id)
        mention_user_ids = self._extract_mention_user_ids(
            text=text,
            channel=channel,
            sender_user_id=str(user_document.get("_id") or ""),
        )
        parent_message_id = str(parent_message_id or "").strip()
        if parent_message_id:
            parent_message = self.message_repository.get_message_by_id(parent_message_id)
            if not parent_message:
                raise ValueError("Parent message not found.")
            if str(parent_message.get("channel_id") or "") != str(channel.get("_id")):
                raise ValueError("Parent message channel mismatch.")

        message_id = self.message_repository.add_message(
            {
                "channel_id": str(channel.get("_id")),
                "user_id": str(user_document.get("_id")),
                "username": str(user_document.get("username") or "member"),
                "profile_image": str(user_document.get("profile_image") or "/static/admin/assets/img/admin.png"),
                "text": text,
                "parent_message_id": parent_message_id or None,
                "reactions": {},
                "reaction_user_ids": [],
                "mention_user_ids": mention_user_ids,
                "is_pinned": False,
                "pinned_at": None,
                "pinned_by_user_id": "",
                "is_deleted": False,
            }
        )
        created_message = self.message_repository.get_message_by_id(message_id)
        return self.serialize_message(
            created_message,
            current_user_id=str(user_document.get("_id")),
            current_account_type=str(user_document.get("account_type") or "member"),
        )

    def update_message(self, user_document: dict, message_id: str, text: str):
        text = str(text or "").strip()
        if not text:
            raise ValueError("Message text is required.")
        if len(text) > 3000:
            raise ValueError("Message text is too long.")

        message, channel = self._get_message_with_access(user_document, message_id)
        if message.get("is_deleted"):
            raise ValueError("Deleted messages cannot be edited.")

        if not self._can_modify_message(user_document, message):
            raise PermissionError("You can only edit your own message.")

        self.message_repository.update_message(
            message_id,
            {
                "text": text,
                "mention_user_ids": self._extract_mention_user_ids(
                    text=text,
                    channel=channel,
                    sender_user_id=str(user_document.get("_id") or ""),
                ),
                "edited_at": datetime.utcnow(),
            },
        )
        updated = self.message_repository.get_message_by_id(message_id)
        return self.serialize_message(
            updated,
            current_user_id=str(user_document.get("_id")),
            current_account_type=str(user_document.get("account_type") or "member"),
        )

    def delete_message(self, user_document: dict, message_id: str):
        message, _ = self._get_message_with_access(user_document, message_id)
        if message.get("is_deleted"):
            return self.serialize_message(
                message,
                current_user_id=str(user_document.get("_id")),
                current_account_type=str(user_document.get("account_type") or "member"),
            )

        if not self._can_modify_message(user_document, message):
            raise PermissionError("You can only delete your own message.")

        self.message_repository.update_message(
            message_id,
            {
                "text": "",
                "is_deleted": True,
                "deleted_at": datetime.utcnow(),
                "reactions": {},
                "is_pinned": False,
                "pinned_at": None,
                "pinned_by_user_id": "",
            },
        )
        updated = self.message_repository.get_message_by_id(message_id)
        return self.serialize_message(
            updated,
            current_user_id=str(user_document.get("_id")),
            current_account_type=str(user_document.get("account_type") or "member"),
        )

    def toggle_message_reaction(self, user_document: dict, message_id: str, emoji: str):
        emoji = str(emoji or "").strip()
        if emoji not in self.ALLOWED_REACTIONS:
            raise ValueError("Unsupported reaction.")

        message, _ = self._get_message_with_access(user_document, message_id)
        if message.get("is_deleted"):
            raise ValueError("Cannot react to a deleted message.")

        user_id = str(user_document.get("_id"))
        reactions = dict(message.get("reactions") or {})
        reacted_user_ids = [str(item) for item in reactions.get(emoji, []) if str(item).strip()]

        if user_id in reacted_user_ids:
            reacted_user_ids = [item for item in reacted_user_ids if item != user_id]
        else:
            reacted_user_ids.append(user_id)

        if reacted_user_ids:
            reactions[emoji] = reacted_user_ids
        elif emoji in reactions:
            reactions.pop(emoji, None)

        reaction_user_ids = sorted(
            {
                str(value)
                for values in reactions.values()
                for value in (values or [])
                if str(value).strip()
            }
        )
        self.message_repository.update_message(
            message_id,
            {
                "reactions": reactions,
                "reaction_user_ids": reaction_user_ids,
                "last_reaction_at": datetime.utcnow(),
            },
        )
        updated = self.message_repository.get_message_by_id(message_id)
        return self.serialize_message(
            updated,
            current_user_id=user_id,
            current_account_type=str(user_document.get("account_type") or "member"),
        )

    def toggle_message_pin(self, user_document: dict, message_id: str):
        message, _ = self._get_message_with_access(user_document, message_id)
        if message.get("is_deleted"):
            raise ValueError("Cannot pin a deleted message.")

        is_pinned = bool(message.get("is_pinned"))
        self.message_repository.update_message(
            message_id,
            {
                "is_pinned": not is_pinned,
                "pinned_at": datetime.utcnow() if not is_pinned else None,
                "pinned_by_user_id": str(user_document.get("_id")) if not is_pinned else "",
            },
        )
        updated = self.message_repository.get_message_by_id(message_id)
        return self.serialize_message(
            updated,
            current_user_id=str(user_document.get("_id")),
            current_account_type=str(user_document.get("account_type") or "member"),
        )

    def create_channel(self, user_document: dict, data: dict):
        if str(user_document.get("account_type") or "").lower() != "admin":
            raise PermissionError("Only server admins can create channels.")

        name = str(data.get("name") or "").strip()
        description = str(data.get("description") or "").strip()
        channel_type = str(data.get("channel_type") or "custom").strip().lower()
        is_public_raw = data.get("is_public", True)
        if isinstance(is_public_raw, str):
            is_public = is_public_raw.strip().lower() in {"1", "true", "yes", "on"}
        else:
            is_public = bool(is_public_raw)

        if not name:
            raise ValueError("Channel name is required.")

        base_slug = self.channel_repository.slugify(name)
        slug = base_slug
        suffix = 1
        while self.channel_repository.get_channel_by_slug(slug):
            suffix += 1
            slug = f"{base_slug}-{suffix}"

        member_ids = []
        if not is_public:
            owner_user_id = str(user_document.get("_id") or "")
            if owner_user_id:
                member_ids.append(owner_user_id)

        channel_id = self.channel_repository.add_channel(
            {
                "name": name,
                "slug": slug,
                "description": description,
                "channel_type": channel_type if channel_type else "custom",
                "is_public": is_public,
                "member_ids": member_ids,
                "created_by_user_id": str(user_document.get("_id")),
            }
        )
        return self.serialize_channel(self.channel_repository.get_channel_by_id(channel_id))

    def update_channel_for_user(self, user_document: dict, channel_id: str, data: dict):
        channel = self._validate_channel_access(user_document, channel_id)
        if not self._can_manage_channel(user_document, channel):
            raise PermissionError("You can only rename your own custom channels.")

        name = str(data.get("name") or "").strip()
        description = str(data.get("description") or "").strip()
        if not name:
            raise ValueError("Channel name is required.")

        self.channel_repository.update_channel(
            str(channel.get("_id")),
            {
                "name": name,
                "description": description,
            },
        )
        return self.serialize_channel(
            self.channel_repository.get_channel_by_id(str(channel.get("_id")))
        )

    def delete_channel_for_user(self, user_document: dict, channel_id: str):
        channel = self._validate_channel_access(user_document, channel_id)
        if not self._can_manage_channel(user_document, channel):
            raise PermissionError("You can only delete your own custom channels.")

        self.message_repository.delete_messages_by_channel(str(channel.get("_id")))
        return self.channel_repository.delete_channel(str(channel.get("_id")))

    def list_files_for_channel(
        self,
        user_document: dict,
        channel_id: str,
        *,
        page: int = 1,
        per_page: int = 50,
        search_query: str = "",
    ):
        channel = self._validate_channel_access(user_document, channel_id)
        safe_page, safe_per_page = self._normalize_pagination(page, per_page, default_per_page=50)
        safe_per_page = min(safe_per_page, 50)
        rows, total = self.file_repository.get_files_page(
            str(channel.get("_id")),
            page=safe_page,
            per_page=safe_per_page,
            search_query=search_query,
        )
        serialized_rows = [self.serialize_file(row, user_document) for row in rows]
        total_pages = (total + safe_per_page - 1) // safe_per_page if total > 0 else 1
        return {
            "files": serialized_rows,
            "file_count": self.file_repository.count_files_for_channel(str(channel.get("_id"))),
            "file_limit": None if self._is_admin_user(user_document) else self.MEMBER_CHANNEL_FILE_LIMIT,
            "pagination": {
                "page": safe_page,
                "per_page": safe_per_page,
                "total_items": total,
                "total_pages": total_pages,
            },
        }

    def upload_file_to_channel(self, user_document: dict, channel_id: str, file_storage, name: str = ""):
        if file_storage is None or not str(getattr(file_storage, "filename", "") or "").strip():
            raise ValueError("Please choose a file to upload.")

        channel = self._validate_channel_access(user_document, channel_id)
        self._assert_file_upload_allowed(user_document, channel, file_storage)

        uploaded_url = self._upload_channel_file(file_storage)
        filename = str(file_storage.filename or "").strip()
        file_id = self.file_repository.add_file(
            {
                "channel_id": str(channel.get("_id")),
                "uploaded_by_user_id": str(user_document.get("_id") or ""),
                "uploaded_by_username": str(user_document.get("username") or "member"),
                "name": str(name or "").strip() or filename,
                "original_filename": filename,
                "file_size": int(self._get_file_size(file_storage)),
                "file_url": uploaded_url,
            }
        )
        created = self.file_repository.get_file_by_id(file_id)
        return self.serialize_file(created, user_document)

    def update_file_in_channel(
        self,
        user_document: dict,
        file_id: str,
        *,
        name: str = "",
        file_storage=None,
    ):
        file_row = self.file_repository.get_file_by_id(file_id)
        if not file_row or file_row.get("is_deleted"):
            raise ValueError("File not found.")

        channel = self._validate_channel_access(user_document, str(file_row.get("channel_id") or ""))
        del channel  # Access check only.
        if not self._can_modify_file(user_document, file_row):
            raise PermissionError("You can only edit your own uploaded files.")

        update_data = {}
        normalized_name = str(name or "").strip()
        if normalized_name:
            update_data["name"] = normalized_name

        if file_storage is not None and str(getattr(file_storage, "filename", "") or "").strip():
            self._assert_file_upload_allowed(
                user_document,
                self.channel_repository.get_channel_by_id(str(file_row.get("channel_id"))),
                file_storage,
                check_channel_quota=False,
            )
            uploaded_url = self._upload_channel_file(file_storage)
            previous_url = str(file_row.get("file_url") or "").strip()
            update_data["file_url"] = uploaded_url
            update_data["original_filename"] = str(file_storage.filename or "").strip() or str(file_row.get("original_filename") or "")
            update_data["file_size"] = int(self._get_file_size(file_storage))
            if previous_url and "res.cloudinary.com" in previous_url and previous_url != uploaded_url:
                cleanup_uploaded_files(raw_url=previous_url)

        if not update_data:
            return self.serialize_file(file_row, user_document)

        self.file_repository.update_file(file_id, update_data)
        updated = self.file_repository.get_file_by_id(file_id)
        return self.serialize_file(updated, user_document)

    def delete_file_in_channel(self, user_document: dict, file_id: str):
        file_row = self.file_repository.get_file_by_id(file_id)
        if not file_row:
            return False

        self._validate_channel_access(user_document, str(file_row.get("channel_id") or ""))
        if not self._can_modify_file(user_document, file_row):
            raise PermissionError("You can only delete your own uploaded files.")

        file_url = str(file_row.get("file_url") or "").strip()
        deleted = self.file_repository.delete_file(file_id)
        if deleted and file_url and "res.cloudinary.com" in file_url:
            cleanup_uploaded_files(raw_url=file_url)
        return deleted

    def get_paginated_users(
        self,
        page: int,
        per_page: int,
        order: SortOrder,
        search_query: str = "",
        account_type_filter: str = "",
    ):
        rows, total = self.user_repository.get_paginated_users(
            page=page,
            per_page=per_page,
            order=order,
            search_query=search_query,
            account_type_filter=account_type_filter,
        )
        return [self.serialize_user(item) for item in rows], total

    def add_user_by_admin(self, data: dict):
        payload = dict(data or {})
        account_type = str(payload.get("account_type") or "member").strip().lower()
        if account_type not in {"admin", "member"}:
            account_type = "member"
        payload["account_type"] = account_type

        user = self.register_account(
            {
                **payload,
                "password": payload.get("password") or "",
            }
        )

        if account_type == "admin":
            self.user_repository.update_user(user["id"], {"account_type": "admin"})
            user = self.serialize_user(self.user_repository.get_user_by_id(user["id"]))
        return user

    def update_user_by_admin(self, user_id: str, data: dict):
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        payload = dict(data or {})
        update_data = {}

        for key in ("name", "birthdate", "place", "gender"):
            if key in payload:
                update_data[key] = str(payload.get(key) or "").strip()

        if "username" in payload:
            username = str(payload.get("username") or "").strip()
            if username and username.lower() != str(user.get("username_lower") or "").lower():
                if self.user_repository.find_by_username(username):
                    raise ValueError("Username is already taken.")
                update_data["username"] = username
                update_data["username_lower"] = username.lower()

        if "email" in payload:
            email = str(payload.get("email") or "").strip()
            if email and email.lower() != str(user.get("email_lower") or "").lower():
                if self.user_repository.find_by_email(email):
                    raise ValueError("Email is already registered.")
                update_data["email"] = email
                update_data["email_lower"] = email.lower()

        if "account_type" in payload:
            account_type = str(payload.get("account_type") or "").strip().lower()
            if account_type in {"admin", "member"}:
                update_data["account_type"] = account_type

        if "is_active" in payload:
            is_active_raw = payload.get("is_active")
            if isinstance(is_active_raw, str):
                update_data["is_active"] = is_active_raw.strip().lower() in {"1", "true", "yes", "on"}
            else:
                update_data["is_active"] = bool(is_active_raw)

        if payload.get("password"):
            password = str(payload.get("password") or "").strip()
            if len(password) < 8:
                raise ValueError("Password must be at least 8 characters.")
            update_data["password"] = generate_password_hash(password)

        self.user_repository.update_user(user_id, update_data)
        return self.serialize_user(self.user_repository.get_user_by_id(user_id))

    def delete_user_by_admin(self, user_id: str):
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            return False

        if user.get("account_type") == "admin" and self.user_repository.count_admin_accounts() <= 1:
            raise ValueError("Cannot delete the last server admin account.")

        # Remove/cleanup concern channels owned by this user.
        concern_channels = list(
            self.channel_repository.collection.find({"owner_user_id": str(user.get("_id"))})
        )
        for channel in concern_channels:
            self.message_repository.delete_messages_by_channel(str(channel.get("_id")))
            self.channel_repository.delete_channel(str(channel.get("_id")))

        # Remove membership from other channels.
        self.channel_repository.collection.update_many(
            {"member_ids": str(user.get("_id"))},
            {"$pull": {"member_ids": str(user.get("_id"))}},
        )

        self.message_repository.delete_messages_by_user(str(user.get("_id")))
        return self.user_repository.delete_user(user_id)

    def get_paginated_channels(
        self,
        page: int,
        per_page: int,
        order: SortOrder,
        search_query: str = "",
        type_filter: str = "",
        visibility_filter: str = "",
    ):
        self.channel_repository.ensure_default_channels()
        rows, total = self.channel_repository.get_paginated_channels(
            page=page,
            per_page=per_page,
            order=order,
            search_query=search_query,
            type_filter=type_filter,
            visibility_filter=visibility_filter,
        )
        return [self.serialize_channel(item) for item in rows], total

    def update_channel_by_admin(self, channel_id: str, data: dict):
        existing = self.channel_repository.get_channel_by_id(channel_id)
        if not existing:
            raise ValueError("Channel not found.")

        payload = dict(data or {})
        update_data = {}

        if "name" in payload:
            name = str(payload.get("name") or "").strip()
            if name:
                update_data["name"] = name

        if "description" in payload:
            update_data["description"] = str(payload.get("description") or "").strip()

        if "channel_type" in payload:
            update_data["channel_type"] = str(payload.get("channel_type") or "custom").strip().lower()

        if "is_public" in payload:
            is_public_raw = payload.get("is_public")
            if isinstance(is_public_raw, str):
                update_data["is_public"] = is_public_raw.strip().lower() in {"1", "true", "yes", "on"}
            else:
                update_data["is_public"] = bool(is_public_raw)

        self.channel_repository.update_channel(channel_id, update_data)
        return self.serialize_channel(self.channel_repository.get_channel_by_id(channel_id))

    def delete_channel_by_admin(self, channel_id: str):
        channel = self.channel_repository.get_channel_by_id(channel_id)
        if not channel:
            return False

        if channel.get("slug") in self.DEFAULT_CHANNEL_SLUGS:
            raise ValueError("Default channels cannot be deleted.")

        self.message_repository.delete_messages_by_channel(str(channel.get("_id")))
        return self.channel_repository.delete_channel(channel_id)

    def get_user_profile_for_channel(self, requester_user: dict, target_user_id: str, channel_id: str):
        channel = self._validate_channel_access(requester_user, channel_id)
        target_user = self.user_repository.get_user_by_id(target_user_id)
        if not target_user or target_user.get("is_active") is False:
            raise ValueError("User not found.")

        if not channel.get("is_public"):
            member_ids = [str(value) for value in (channel.get("member_ids") or []) if str(value).strip()]
            if str(target_user.get("_id") or "") not in member_ids:
                raise PermissionError("User is not part of this private channel.")

        serialized_user = self.serialize_user(target_user)
        serialized_user["bio"] = (
            f"{serialized_user.get('name') or serialized_user.get('username')} "
            f"is a {serialized_user.get('account_type', 'member')} account."
        )
        return serialized_user

    def _is_admin_user(self, user_document: dict):
        return str(user_document.get("account_type") or "").strip().lower() == "admin"

    def _can_modify_file(self, user_document: dict, file_row: dict):
        if self._is_admin_user(user_document):
            return True
        return str(file_row.get("uploaded_by_user_id") or "") == str(user_document.get("_id") or "")

    def _assert_file_upload_allowed(
        self,
        user_document: dict,
        channel: dict,
        file_storage,
        *,
        check_channel_quota: bool = True,
    ):
        if self._is_admin_user(user_document):
            return

        if not channel:
            raise ValueError("Channel not found.")

        if check_channel_quota:
            channel_id = str(channel.get("_id") or "").strip()
            current_count = self.file_repository.count_files_for_channel(channel_id)
            if current_count >= self.MEMBER_CHANNEL_FILE_LIMIT:
                raise ValueError(
                    f"Channel file limit reached ({self.MEMBER_CHANNEL_FILE_LIMIT}). Delete old files first."
                )

        file_size = self._get_file_size(file_storage)
        if file_size > self.MEMBER_FILE_SIZE_LIMIT_BYTES:
            raise ValueError("File exceeds 1MB limit.")

    @staticmethod
    def _get_file_size(file_storage):
        try:
            current_pos = file_storage.stream.tell()
            file_storage.stream.seek(0, os.SEEK_END)
            size = file_storage.stream.tell()
            file_storage.stream.seek(current_pos, os.SEEK_SET)
            return int(size or 0)
        except Exception:
            return 0

    def _upload_channel_file(self, file_storage):
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)
        file_storage.save(temp_path)
        uploaded_url = None
        try:
            uploaded_url = upload_file_to_cloudinary(
                temp_path,
                resource_type=CloudinaryResourceType.RAW,
                folder=CloudinaryFolders.DEFAULT,
            )
            if str(uploaded_url or "").lower().startswith("error "):
                raise ValueError(uploaded_url)
            return uploaded_url
        except Exception:
            if uploaded_url and "res.cloudinary.com" in str(uploaded_url):
                cleanup_uploaded_files(raw_url=uploaded_url)
            raise
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _extract_mention_user_ids(self, text: str, channel: dict, sender_user_id: str = ""):
        usernames = {
            str(match.group(1) or "").strip().lower()
            for match in self.MENTION_PATTERN.finditer(str(text or ""))
            if str(match.group(1) or "").strip()
        }
        if not usernames:
            return []

        query = {
            "username_lower": {"$in": list(usernames)},
            "is_active": {"$ne": False},
        }
        users = list(self.user_repository.collection.find(query, {"_id": 1, "username_lower": 1}))
        if not channel.get("is_public"):
            member_ids = {str(value) for value in (channel.get("member_ids") or []) if str(value).strip()}
            users = [item for item in users if str(item.get("_id") or "") in member_ids]

        mention_user_ids = [str(item.get("_id") or "") for item in users if item.get("_id")]
        if sender_user_id:
            mention_user_ids = [value for value in mention_user_ids if value != sender_user_id]
        return mention_user_ids

    def _is_message_mentioning_user(self, message_row: dict, user_id: str, username: str):
        normalized_user_id = str(user_id or "").strip()
        normalized_username = str(username or "").strip().lower()
        mention_user_ids = [str(value) for value in (message_row.get("mention_user_ids") or []) if str(value).strip()]
        if normalized_user_id and normalized_user_id in mention_user_ids:
            return True
        if not normalized_username:
            return False
        return bool(re.search(rf"(?<![\\w])@{re.escape(normalized_username)}\\b", str(message_row.get("text") or ""), flags=re.IGNORECASE))

    def _can_manage_channel(self, user_document: dict, channel: dict):
        account_type = str(user_document.get("account_type") or "").strip().lower()
        if account_type != "admin":
            return False

        if str(channel.get("slug") or "") in self.DEFAULT_CHANNEL_SLUGS:
            return False

        channel_creator = str(channel.get("created_by_user_id") or "").strip()
        if not channel_creator:
            return False

        return channel_creator == str(user_document.get("_id") or "").strip()

    def _validate_channel_access(self, user_document: dict, channel_id: str):
        channel = self.channel_repository.get_channel_by_id(channel_id)
        if not channel:
            raise ValueError("Channel not found.")

        user_id = str(user_document.get("_id"))
        account_type = str(user_document.get("account_type") or "member").lower()
        if account_type == "admin":
            return channel

        if channel.get("is_public"):
            return channel

        if user_id in (channel.get("member_ids") or []):
            return channel

        raise PermissionError("You do not have access to this channel.")

    def _get_message_with_access(self, user_document: dict, message_id: str):
        message = self.message_repository.get_message_by_id(message_id)
        if not message:
            raise ValueError("Message not found.")

        channel_id = str(message.get("channel_id") or "")
        channel = self._validate_channel_access(user_document, channel_id)
        return message, channel

    @staticmethod
    def _can_modify_message(user_document: dict, message: dict):
        account_type = str(user_document.get("account_type") or "member").lower()
        if account_type == "admin":
            return True
        return str(message.get("user_id") or "") == str(user_document.get("_id") or "")

    @classmethod
    def _is_user_online(cls, user_document: dict):
        if not user_document:
            return False

        last_active_at = user_document.get("last_active_at")
        if not isinstance(last_active_at, datetime):
            return bool(user_document.get("is_online"))

        elapsed = datetime.utcnow() - last_active_at
        return elapsed <= timedelta(seconds=cls.ONLINE_WINDOW_SECONDS)

    @staticmethod
    def _env_bool(name: str, default_value: bool = False):
        raw = os.getenv(name)
        if raw is None:
            return bool(default_value)
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _mask_email(email: str):
        value = str(email or "").strip()
        if "@" not in value:
            return value
        local, domain = value.split("@", 1)
        if len(local) <= 2:
            local_masked = f"{local[:1]}***"
        else:
            local_masked = f"{local[:2]}***"
        return f"{local_masked}@{domain}"

    def _send_smtp_email(self, recipient_email: str, subject: str, body: str, html_body: str = ""):
        smtp_host = str(os.getenv("SMTP_HOST") or "").strip()
        smtp_username = str(os.getenv("SMTP_USERNAME") or "").strip()
        smtp_password = str(os.getenv("SMTP_PASSWORD") or "").strip()
        smtp_from_email = str(os.getenv("SMTP_FROM_EMAIL") or smtp_username).strip()
        smtp_from_name = str(os.getenv("SMTP_FROM_NAME") or "Server Community").strip()

        if not smtp_host or not smtp_from_email:
            raise ValueError("SMTP is not configured. Set SMTP_HOST and SMTP_FROM_EMAIL in env.")

        try:
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
        except Exception:
            smtp_port = 587

        use_ssl = self._env_bool("SMTP_USE_SSL", False)
        use_tls = self._env_bool("SMTP_USE_TLS", not use_ssl)

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{smtp_from_name} <{smtp_from_email}>"
        message["To"] = recipient_email
        message.set_content(body)
        if str(html_body or "").strip():
            message.add_alternative(str(html_body), subtype="html")

        try:
            if use_ssl:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as smtp:
                    if smtp_username and smtp_password:
                        smtp.login(smtp_username, smtp_password)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
                    smtp.ehlo()
                    if use_tls:
                        smtp.starttls()
                        smtp.ehlo()
                    if smtp_username and smtp_password:
                        smtp.login(smtp_username, smtp_password)
                    smtp.send_message(message)
        except Exception as exc:
            raise ValueError(f"Failed to send OTP email: {exc}") from exc

    @staticmethod
    def _build_otp_email_html(recipient_name: str, otp_code: str, expiry_minutes: int):
        safe_name = str(recipient_name or "Member")
        safe_code = str(otp_code or "").strip()
        safe_minutes = int(expiry_minutes or 10)
        return f"""
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#041427;font-family:Arial,sans-serif;color:#e9f7ff;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#041427;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:linear-gradient(160deg,#072338,#031521);border:1px solid rgba(93,227,255,.35);border-radius:16px;overflow:hidden;">
            <tr>
              <td style="padding:20px 24px;background:linear-gradient(120deg,#0b3a56,#0c2539);border-bottom:1px solid rgba(93,227,255,.25);">
                <h2 style="margin:0;font-size:22px;line-height:1.2;color:#dff8ff;">Server Community OTP</h2>
                <p style="margin:6px 0 0 0;font-size:13px;color:#9ed7ea;">Secure password reset verification</p>
              </td>
            </tr>
            <tr>
              <td style="padding:22px 24px;">
                <p style="margin:0 0 14px 0;font-size:15px;color:#d5f4ff;">Hi {safe_name},</p>
                <p style="margin:0 0 16px 0;font-size:14px;line-height:1.6;color:#bfe8f7;">
                  Use the one-time password below to reset your Server Community account password.
                </p>
                <div style="margin:0 0 14px 0;padding:14px 16px;border:1px solid rgba(116,233,255,.45);border-radius:12px;background:rgba(2,20,34,.75);text-align:center;">
                  <span style="display:block;font-size:30px;letter-spacing:8px;font-weight:700;color:#72eaff;">{safe_code}</span>
                </div>
                <p style="margin:0;font-size:13px;color:#a8d8ea;">
                  This OTP expires in <strong style="color:#dff8ff;">{safe_minutes} minutes</strong>.
                </p>
                <p style="margin:14px 0 0 0;font-size:12px;color:#86bed3;">
                  If you did not request this reset, you can ignore this email.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
        """

    def _verify_firebase_id_token(self, id_token: str):
        id_token = str(id_token or "").strip()
        if not id_token:
            raise ValueError("Missing Google authentication token.")

        firebase_api_key = str(os.getenv("FIREBASE_API_KEY") or "").strip()
        if not firebase_api_key:
            raise ValueError("Firebase is not configured. Set FIREBASE_API_KEY in env.")

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={firebase_api_key}"
        try:
            response = requests.post(url, json={"idToken": id_token}, timeout=12)
        except requests.RequestException as exc:
            raise ValueError("Failed to verify Google token.") from exc

        try:
            payload = response.json()
        except Exception as exc:
            raise ValueError("Invalid Firebase verification response.") from exc

        if response.status_code != 200:
            message = str((payload.get("error") or {}).get("message") or "Google authentication failed.")
            if message == "INVALID_ID_TOKEN":
                message = "Invalid Google token. Please login again."
            elif message == "TOKEN_EXPIRED":
                message = "Google token expired. Please login again."
            raise ValueError(message)

        users = payload.get("users") or []
        if not users:
            raise ValueError("Invalid Google authentication response.")
        return users[0]

    def _generate_unique_username(self, seed: str):
        seed = str(seed or "").strip().lower()
        base = "".join(ch for ch in seed if ch.isalnum()) or "member"
        base = base[:18]

        candidate = base
        index = 1
        while self.user_repository.find_by_username(candidate):
            index += 1
            suffix = str(index)
            candidate = f"{base[: max(1, 20 - len(suffix))]}{suffix}"
        return candidate

    def _create_google_user(self, google_user: dict):
        email = str(google_user.get("email") or "").strip()
        display_name = str(google_user.get("displayName") or "").strip() or email.split("@")[0]
        username = self._generate_unique_username(email.split("@")[0] or display_name)
        profile_image = str(google_user.get("photoUrl") or "").strip() or "/static/admin/assets/img/admin.png"

        user_id = self.user_repository.add_user(
            {
                "name": display_name,
                "username": username,
                "username_lower": username.lower(),
                "email": email,
                "email_lower": email.lower(),
                "password": generate_password_hash(secrets.token_urlsafe(24)),
                "birthdate": "",
                "place": "",
                "gender": "",
                "profile_image": profile_image,
                "account_type": "member",
                "is_active": True,
                "is_online": False,
                "last_active_at": None,
                "google_uid": str(google_user.get("localId") or "").strip(),
                "auth_provider": "google",
            }
        )
        return self.user_repository.get_user_by_id(user_id)

    def _sync_existing_google_user(self, user: dict, google_user: dict):
        update_data = {}
        google_uid = str(google_user.get("localId") or "").strip()
        if google_uid and str(user.get("google_uid") or "").strip() != google_uid:
            update_data["google_uid"] = google_uid
            update_data["auth_provider"] = "google"

        if not str(user.get("name") or "").strip():
            display_name = str(google_user.get("displayName") or "").strip()
            if display_name:
                update_data["name"] = display_name

        photo_url = str(google_user.get("photoUrl") or "").strip()
        if photo_url and not str(user.get("profile_image") or "").strip():
            update_data["profile_image"] = photo_url

        if update_data:
            self.user_repository.update_user(str(user.get("_id")), update_data)

    def _upload_profile_image(self, image_file):
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)
        image_file.save(temp_path)

        webp_path = convert_to_webp(temp_path)
        uploaded_url = None
        try:
            uploaded_url = upload_file_to_cloudinary(
                webp_path,
                resource_type=CloudinaryResourceType.IMAGE,
                folder=CloudinaryFolders.DEFAULT,
            )
            return uploaded_url
        except Exception:
            cleanup_uploaded_files(None, uploaded_url)
            raise
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if webp_path != temp_path and os.path.exists(webp_path):
                os.remove(webp_path)

    @classmethod
    def serialize_user(cls, item: dict):
        if not item:
            return None
        last_active_at = item.get("last_active_at")
        return {
            "id": str(item.get("_id")),
            "name": str(item.get("name") or ""),
            "username": str(item.get("username") or ""),
            "email": str(item.get("email") or ""),
            "birthdate": str(item.get("birthdate") or ""),
            "place": str(item.get("place") or ""),
            "gender": str(item.get("gender") or ""),
            "profile_image": str(item.get("profile_image") or "/static/admin/assets/img/admin.png"),
            "account_type": str(item.get("account_type") or "member"),
            "is_active": item.get("is_active") is not False,
            "is_online": cls._is_user_online(item),
            "last_active_at": last_active_at.isoformat() + "Z" if isinstance(last_active_at, datetime) else None,
            "created_at": item.get("created_at").isoformat() + "Z" if item.get("created_at") else None,
        }

    @staticmethod
    def serialize_channel(item: dict):
        if not item:
            return None
        return {
            "id": str(item.get("_id")),
            "name": str(item.get("name") or ""),
            "slug": str(item.get("slug") or ""),
            "description": str(item.get("description") or ""),
            "channel_type": str(item.get("channel_type") or "custom"),
            "is_public": bool(item.get("is_public", True)),
            "member_ids": list(item.get("member_ids") or []),
            "owner_user_id": str(item.get("owner_user_id") or ""),
            "created_by_user_id": str(item.get("created_by_user_id") or ""),
            "created_at": item.get("created_at").isoformat() + "Z" if item.get("created_at") else None,
        }

    @staticmethod
    def serialize_file(item: dict, current_user: dict = None):
        if not item:
            return None
        current_user_id = str((current_user or {}).get("_id") or (current_user or {}).get("id") or "").strip()
        current_account_type = str((current_user or {}).get("account_type") or "member").strip().lower()
        is_admin = current_account_type == "admin"
        owner_id = str(item.get("uploaded_by_user_id") or "").strip()
        can_modify = is_admin or (current_user_id and current_user_id == owner_id)
        return {
            "id": str(item.get("_id")),
            "channel_id": str(item.get("channel_id") or ""),
            "name": str(item.get("name") or item.get("original_filename") or "file"),
            "original_filename": str(item.get("original_filename") or ""),
            "file_url": str(item.get("file_url") or ""),
            "file_size": int(item.get("file_size") or 0),
            "uploaded_by_user_id": owner_id,
            "uploaded_by_username": str(item.get("uploaded_by_username") or "member"),
            "editable": can_modify,
            "deletable": can_modify,
            "created_at": item.get("created_at").isoformat() + "Z" if item.get("created_at") else None,
            "updated_at": item.get("updated_at").isoformat() + "Z" if item.get("updated_at") else None,
        }

    @staticmethod
    def serialize_message(item: dict, current_user_id: str = "", current_account_type: str = "member"):
        if not item:
            return None
        reactions_payload = {}
        raw_reactions = item.get("reactions") or {}
        for emoji, user_ids in raw_reactions.items():
            normalized_user_ids = [str(value) for value in (user_ids or []) if str(value).strip()]
            if not normalized_user_ids:
                continue
            reactions_payload[str(emoji)] = {
                "count": len(normalized_user_ids),
                "reacted": str(current_user_id) in normalized_user_ids if current_user_id else False,
            }

        is_deleted = bool(item.get("is_deleted"))
        is_admin = str(current_account_type or "").lower() == "admin"
        is_owner = str(item.get("user_id") or "") == str(current_user_id or "")
        can_modify = (is_admin or is_owner) and not is_deleted

        return {
            "id": str(item.get("_id")),
            "channel_id": str(item.get("channel_id") or ""),
            "user_id": str(item.get("user_id") or ""),
            "username": str(item.get("username") or ""),
            "profile_image": str(item.get("profile_image") or "/static/admin/assets/img/admin.png"),
            "text": "This message was deleted." if is_deleted else str(item.get("text") or ""),
            "raw_text": str(item.get("text") or ""),
            "is_deleted": is_deleted,
            "parent_message_id": str(item.get("parent_message_id") or ""),
            "mention_user_ids": [str(value) for value in (item.get("mention_user_ids") or []) if str(value).strip()],
            "mentioned_me": str(current_user_id or "") in [str(value) for value in (item.get("mention_user_ids") or []) if str(value).strip()],
            "is_pinned": bool(item.get("is_pinned")),
            "pinned_at": item.get("pinned_at").isoformat() + "Z" if item.get("pinned_at") else None,
            "reactions": reactions_payload,
            "editable": can_modify,
            "deletable": can_modify,
            "created_at": item.get("created_at").isoformat() + "Z" if item.get("created_at") else None,
            "edited_at": item.get("edited_at").isoformat() + "Z" if item.get("edited_at") else None,
        }
