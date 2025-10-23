from Services.AuthService import AuthService
from Repositories.AuthRepository import AuthRepository

# Initialize Services
auth_service = AuthService(repository=AuthRepository())

# ************************** API Controller ********************************

def update_profile_route():
    return auth_service.update_profile()