class Portfolio:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email
        }
