from Repositories.Interfaces.ILoginAttemptRepository import ILoginAttemptRepository
from Models.LoginAttempt import LoginAttempt
from datetime import datetime, timedelta
from dateutil import parser

class LoginAttemptService:
    def __init__(self, repository: ILoginAttemptRepository):
        self.repository = repository

    # -------------------------- LoginAttempt Service Methods -------------------------

    def get_login_attempt_by_id(self, login_attempt_id: str):
        return self.repository.get_login_attempt_by_id(login_attempt_id)

    def get_paginated_login_attempt_list(self, page, per_page, order):
        data, total_data = self.repository.get_paginated_login_attempt_list(page, per_page, order)
        system_info_list = []

        for login_attempt in data:
            lockout_value = login_attempt.get("lockout_until")

            if lockout_value:
                try:
                    # Detect if it's string or datetime
                    if isinstance(lockout_value, str):
                        utc_dt = parser.isoparse(lockout_value)
                    elif isinstance(lockout_value, datetime):
                        utc_dt = lockout_value
                    else:
                        raise TypeError(f"Unsupported type: {type(lockout_value)}")

                    # ✅ Convert UTC → Philippine Time (UTC+8)
                    ph_dt = utc_dt + timedelta(hours=8)

                    # Format cleanly
                    login_attempt["lockout_until"] = ph_dt.strftime("%Y-%m-%d %I:%M %p")

                except Exception as e:
                    print(f"Datetime conversion error ({lockout_value}): {e}")

            system_info_list.append(LoginAttempt.from_dict(login_attempt))

        return system_info_list, total_data

    def delete_login_attempt(self, login_attempt_id: str):
        existing_login_attempt = self.get_login_attempt_by_id(login_attempt_id)
        if not existing_login_attempt:
            return False

        return self.repository.delete_login_attempt(login_attempt_id)

