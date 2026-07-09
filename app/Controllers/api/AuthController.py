from app.Services.AuthService import AuthService
from app.Repositories.AuthRepository import AuthRepository
from app.Repositories.LoginAttemptRepository import LoginAttemptRepository
from app.Requests.api.AuthRequest import AuthRequest

# Initialize Services
auth_service = AuthService(
    repository=AuthRepository(),
    attempt_repository=LoginAttemptRepository()
)

# ************************** API Controller ********************************

def update_profile_route():
    form = AuthRequest()
    _, error_response, status_code = form.validated()
    if error_response:
        return error_response, status_code

    return auth_service.update_profile()