from flask import jsonify, request, session
from werkzeug.security import check_password_hash
from backend.Repositories.Interfaces.IAuthRepository import IAuthRepository
from backend.Repositories.Interfaces.ILoginAttemptRepository import ILoginAttemptRepository
from backend.Repositories.LoginAttemptRepository import MAX_ATTEMPTS
from werkzeug.security import generate_password_hash
from datetime import datetime

from backend.constants.messages import INVALID_USE_OR_PASS_ERROR, LOGIN_ATTEMPT_LOCKED_MSG, LOGIN_SUCCESS_MSG, MANY_FAILED_ATTEMPTS_ERROR, PROFILE_UPDATE_MSG, UNAUTHORIZED_ACCESS_ERROR, USER_NOT_FOUND_ERROR

class AuthService:
    def __init__(self, repository: IAuthRepository, attempt_repository: ILoginAttemptRepository):
        self.repository = repository
        self.login_attempt_repo = attempt_repository

    def authenticate_admin(self, username: str, password: str):
        attempt_info = self.login_attempt_repo.get_attempt_info()
        now = datetime.utcnow()

        # ✅ Check for lockout first
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

        # verify password hash
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

        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user_id = session.get('user_id')
        user = self.repository.find_by_id(user_id)

        if not user:
            return jsonify({"message": USER_NOT_FOUND_ERROR}), 404

        update_data = {"username": username}
        if password and password.strip() != "":
            update_data["password"] = generate_password_hash(password)

        self.repository.update_user(user_id, update_data)

        return jsonify({"message": PROFILE_UPDATE_MSG}), 200
