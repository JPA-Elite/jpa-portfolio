from abc import ABC, abstractmethod

class IAuthRepository(ABC):
    @abstractmethod
    def find_by_username(self, username: str):
        pass

    @abstractmethod
    def find_by_id(self, id):
        pass

    @abstractmethod
    def update_user(self, id, data: dict):
        pass

    @abstractmethod
    def get_face_records(self, id):
        pass

    @abstractmethod
    def update_face_reference(self, id, face_crop_b64: str, registered_at: str):
        pass

    @abstractmethod
    def update_face_verified(self, id, verified_at: str, distance: float):
        pass

    @abstractmethod
    def get_user_email(self, id):
        pass