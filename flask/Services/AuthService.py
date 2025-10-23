from flask import jsonify, request, session
from werkzeug.security import check_password_hash
from Repositories.Interfaces.IAuthRepository import IAuthRepository
from werkzeug.security import generate_password_hash

class AuthService:
    def __init__(self, repository: IAuthRepository):
        self.repository = repository

    def authenticate_admin(self, username: str, password: str):
        """Return user dict if credentials are valid, else None"""
        user = self.repository.find_by_username(username)
        if not user:
            return None

        # verify password hash
        if check_password_hash(user["password"], password):
            return user
        return None


    def update_profile(self):
        if 'user_id' not in session:
            return jsonify({"message": "Unauthorized access"}), 401

        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user_id = session.get('user_id')
        user = self.repository.find_by_id(user_id)

        if not user:
            return jsonify({"message": "User not found"}), 404

        update_data = {"username": username}
        if password and password.strip() != "":
            update_data["password"] = generate_password_hash(password)

        self.repository.update_user(user_id, update_data)

        return jsonify({"message": "Profile updated successfully!"}), 200
