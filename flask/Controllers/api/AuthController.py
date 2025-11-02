from Services.AuthService import AuthService
from Repositories.AuthRepository import AuthRepository
from Repositories.LoginAttemptRepository import LoginAttemptRepository

# Initialize Services
auth_service = AuthService(
    repository=AuthRepository(),
    attempt_repository=LoginAttemptRepository()
)

# ************************** API Controller ********************************

def update_profile_route():
    return auth_service.update_profile()