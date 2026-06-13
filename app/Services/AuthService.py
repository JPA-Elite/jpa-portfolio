from flask import jsonify, request, session
from werkzeug.security import check_password_hash
from app.Repositories.Interfaces.IAuthRepository import IAuthRepository
from app.Repositories.Interfaces.ILoginAttemptRepository import ILoginAttemptRepository
from app.Repositories.LoginAttemptRepository import MAX_ATTEMPTS
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
import tempfile
from app.constants.messages import INVALID_USE_OR_PASS_ERROR, LOGIN_ATTEMPT_LOCKED_MSG, LOGIN_SUCCESS_MSG, MANY_FAILED_ATTEMPTS_ERROR, PROFILE_UPDATE_MSG, UNAUTHORIZED_ACCESS_ERROR, USER_NAME_REQUIRED_ERROR, USER_NOT_FOUND_ERROR
from app.constants.cloudinary import CloudinaryFolders, CloudinaryResourceType
from app.utils import cleanup_uploaded_files, convert_to_webp, upload_file_to_cloudinary
from app.extensions import cache

class AuthService:
    def __init__(self, repository: IAuthRepository, attempt_repository: ILoginAttemptRepository):
        self.repository = repository
        self.login_attempt_repo = attempt_repository

    def authenticate_admin(self, username: str, password: str):
        attempt_info = self.login_attempt_repo.get_attempt_info()
        now = datetime.utcnow()

        if attempt_info and attempt_info.get("lockout_until"):
            lockout_until = attempt_info["lockout_until"]
            if lockout_until and now < lockout_until:
                remaining = int((lockout_until - now).total_seconds() // 60)
                return None, LOGIN_ATTEMPT_LOCKED_MSG.format(minutes=remaining), True

        user = self.repository.find_by_username(username)
        if not user:
            self.login_attempt_repo.update_attempt(success=False)
            remaining = MAX_ATTEMPTS - (attempt_info.get("attempts", 0) + 1)
            return None, INVALID_USE_OR_PASS_ERROR.format(attempts=remaining), False

        if check_password_hash(user["password"], password):
            self.login_attempt_repo.update_attempt(success=True)
            return user, LOGIN_SUCCESS_MSG, False
        else:
            updated = self.login_attempt_repo.update_attempt(success=False)
            if updated.get("lockout_until"):
                return None, MANY_FAILED_ATTEMPTS_ERROR, True
            remaining = MAX_ATTEMPTS - updated["attempts"]
            return None, INVALID_USE_OR_PASS_ERROR.format(attempts=remaining), False

    def update_profile(self):
        if 'user_id' not in session:
            return jsonify({"message": UNAUTHORIZED_ACCESS_ERROR}), 401

        data = request.get_json(silent=True) or request.form
        username = (data.get('username') or "").strip()
        password = (data.get('password') or "").strip()
        profile_image_file = request.files.get("profile_image_file")

        user_id = session.get('user_id')
        user = self.repository.find_by_id(user_id)

        if not user:
            return jsonify({"message": USER_NOT_FOUND_ERROR}), 404

        if not username:
            return jsonify({"message": USER_NAME_REQUIRED_ERROR}), 400

        update_data = {"username": username}
        if password:
            update_data["password"] = generate_password_hash(password)

        new_profile_image = None
        existing_profile_image = user.get("profile_image")
        try:
            if profile_image_file:
                fd, path = tempfile.mkstemp()
                os.close(fd)
                profile_image_file.save(path)

                webp_path = convert_to_webp(path)
                new_profile_image = upload_file_to_cloudinary(
                    webp_path,
                    resource_type=CloudinaryResourceType.IMAGE,
                    folder=CloudinaryFolders.DEFAULT
                )

                os.remove(path)
                if webp_path != path:
                    os.remove(webp_path)

                update_data["profile_image"] = new_profile_image

            self.repository.update_user(user_id, update_data)
        except Exception as error:
            cleanup_uploaded_files(None, new_profile_image)
            return jsonify({"message": f"Failed to update profile image: {error}"}), 500

        if new_profile_image and existing_profile_image and str(existing_profile_image).startswith("http"):
            cleanup_uploaded_files(None, existing_profile_image)

        session["username"] = update_data.get("username", session.get("username"))
        if new_profile_image:
            session["profile_image"] = new_profile_image
        self._clear_admin_page_cache()

        return jsonify({
            "message": PROFILE_UPDATE_MSG,
            "username": session.get("username"),
            "profile_image": session.get("profile_image"),
        }), 200

    @staticmethod
    def _clear_admin_page_cache():
        for key in (
            "admin_page_dashboard",
            "admin_page_gallery",
            "admin_page_video",
            "admin_page_music",
            "admin_page_key_projects",
            "admin_page_company_roadmaps",
            "admin_page_settings",
            "admin_page_login_attempts",
        ):
            try:
                cache.delete(key)
            except Exception:
                pass

