from werkzeug.security import check_password_hash
from Repositories.Interfaces.IAuthRepository import IAuthRepository

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
