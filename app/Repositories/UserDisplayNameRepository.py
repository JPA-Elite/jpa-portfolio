from app.Repositories.BaseRepository import BaseRepository
from app.Repositories.Interfaces.IUserDisplayNameRepository import IUserDisplayNameRepository
from app.constants.db_collections import MongoCollections as mc


class UserDisplayNameRepository(IUserDisplayNameRepository, BaseRepository):
    def __init__(self):
        super().__init__(mc.USER_NAMES)

    def find_by_ip(self, ip_address: str):
        return self.find_one({"ip_address": ip_address})

    def find_display_names_by_ips(self, ip_addresses: list[str]):
        if not ip_addresses:
            return {}

        docs = self.find(
            {"ip_address": {"$in": ip_addresses}},
            projection={"ip_address": 1, "display_name": 1},
        )

        return {
            doc.get("ip_address"): doc.get("display_name")
            for doc in docs
            if doc.get("display_name")
        }

    def find_profiles_by_ips(self, ip_addresses: list[str]):
        if not ip_addresses:
            return {}

        docs = self.find(
            {"ip_address": {"$in": ip_addresses}},
            projection={"ip_address": 1, "display_name": 1, "avatar_url": 1},
        )

        return {
            doc.get("ip_address"): {
                "display_name": doc.get("display_name"),
                "avatar_url": doc.get("avatar_url"),
            }
            for doc in docs
        }

    def upsert_display_name(self, ip_address: str, display_name: str, change_count: int, changed_date: str):
        return self.update_one(
            {"ip_address": ip_address},
            {
                "$set": {
                    "ip_address": ip_address,
                    "display_name": display_name,
                    "change_count": change_count,
                    "changed_date": changed_date,
                }
            },
            upsert=True,
        )

    def upsert_avatar(self, ip_address: str, avatar_url: str, change_count: int, changed_date: str):
        return self.update_one(
            {"ip_address": ip_address},
            {
                "$set": {
                    "ip_address": ip_address,
                    "avatar_url": avatar_url,
                    "avatar_change_count": change_count,
                    "avatar_changed_date": changed_date,
                }
            },
            upsert=True,
        )
