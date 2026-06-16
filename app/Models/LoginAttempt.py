class LoginAttempt:
    def __init__(self, attempts, lockout_until, _id=None):
        self._id = _id
        self.attempts = attempts
        self.lockout_until = lockout_until

    def to_dict(self):
        data = {
            "attempts": self.attempts,
            "lockout_until": self.lockout_until,
        }

        if self._id is not None:
            data["_id"] = str(self._id)

        return data

    @staticmethod
    def from_dict(data):
        return LoginAttempt(
            _id=data.get("_id"),
            attempts=data.get("attempts"),
            lockout_until=data.get("lockout_until"),
        )
