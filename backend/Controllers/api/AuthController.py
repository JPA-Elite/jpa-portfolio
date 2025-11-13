from backend.Services.AuthService import AuthService
from backend.Repositories.AuthRepository import AuthRepository
from backend.Repositories.LoginAttemptRepository import LoginAttemptRepository

# Initialize Services
auth_service = AuthService(
    repository=AuthRepository(),
    attempt_repository=LoginAttemptRepository()
)

# ************************** API Controller ********************************

def update_profile_route():
    return auth_service.update_profile()