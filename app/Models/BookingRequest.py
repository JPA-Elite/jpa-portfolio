from datetime import datetime

class BookingRequest:
    def __init__(self, name, email, preferred_date, preferred_time, message, ip_address, created_at=None, read=False, service=None, _id=None):
        self._id = _id
        self.name = name
        self.email = email
        self.preferred_date = preferred_date
        self.preferred_time = preferred_time
        self.message = message
        self.ip_address = ip_address
        self.created_at = created_at or datetime.utcnow()
        self.read = read
        self.service = service

    def to_dict(self):
        data = {
            "name": self.name,
            "email": self.email,
            "preferred_date": self.preferred_date,
            "preferred_time": self.preferred_time,
            "message": self.message,
            "ip_address": self.ip_address,
            "created_at": self.created_at,
            "read": self.read,
            "service": self.service,
        }
        if self._id is not None:
            data["_id"] = str(self._id)
        return data

    @staticmethod
    def from_dict(data):
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except (ValueError, TypeError):
                created_at = datetime.utcnow()
        return BookingRequest(
            _id=data.get("_id"),
            name=data.get("name", ""),
            email=data.get("email", ""),
            preferred_date=data.get("preferred_date", ""),
            preferred_time=data.get("preferred_time", ""),
            message=data.get("message", ""),
            ip_address=data.get("ip_address", ""),
            created_at=created_at,
            read=data.get("read", False),
            service=data.get("service"),
        )
