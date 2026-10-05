from datetime import date

from app.Models.UserDisplayName import UserDisplayName
from app.Repositories.Interfaces.IUserDisplayNameRepository import IUserDisplayNameRepository


class UserDisplayNameService:
    DAILY_NAME_CHANGE_LIMIT = 20
    DAILY_AVATAR_CHANGE_LIMIT = 20
    MAX_NAME_LENGTH = 30

    def __init__(self, repository: IUserDisplayNameRepository):
        self.repository = repository

    def _normalize_record(self, record):
        if not isinstance(record, dict):
            return record
        return UserDisplayName.from_dict(record).to_dict()

    def _normalize_ip(self, ip_address):
        if not ip_address:
            return ip_address
        if "," in ip_address:
            return ip_address.split(",")[0].strip()
        return ip_address.strip()

    def get_display_name(self, ip_address):
        ip_address = self._normalize_ip(ip_address)
        record = self._normalize_record(self.repository.find_by_ip(ip_address))
        if not record:
            return None, self.DAILY_NAME_CHANGE_LIMIT
        return record.get("display_name"), self._remaining_changes(record)

    def get_profile(self, ip_address):
        ip_address = self._normalize_ip(ip_address)
        record = self._normalize_record(self.repository.find_by_ip(ip_address))
        if not record:
            return None, None, self.DAILY_NAME_CHANGE_LIMIT
        return record.get("display_name"), record.get("avatar_url"), self._remaining_changes(record)

    def get_display_names_map(self, ip_addresses):
        normalized = [ip.strip() for ip in (ip_addresses or []) if ip and ip.strip()]
        if not normalized:
            return {}
        return self.repository.find_display_names_by_ips(normalized)

    def get_profiles_map(self, ip_addresses):
        normalized = [ip.strip() for ip in (ip_addresses or []) if ip and ip.strip()]
        if not normalized:
            return {}
        return self.repository.find_profiles_by_ips(normalized)

    def save_display_name(self, ip_address, display_name):
        ip_address = self._normalize_ip(ip_address)
        display_name = display_name.strip()[: self.MAX_NAME_LENGTH]
        today = date.today().isoformat()
        record = self._normalize_record(self.repository.find_by_ip(ip_address))

        if not record:
            self.repository.upsert_display_name(ip_address, display_name, 1, today)
            return display_name, self.DAILY_NAME_CHANGE_LIMIT - 1

        if record.get("display_name") == display_name:
            return display_name, self._remaining_changes(record)

        if record.get("changed_date") != today:
            self.repository.upsert_display_name(ip_address, display_name, 1, today)
            return display_name, self.DAILY_NAME_CHANGE_LIMIT - 1

        change_count = int(record.get("change_count") or 0)
        if change_count >= self.DAILY_NAME_CHANGE_LIMIT:
            return None, 0

        change_count += 1
        self.repository.upsert_display_name(ip_address, display_name, change_count, today)
        return display_name, self.DAILY_NAME_CHANGE_LIMIT - change_count

    def get_avatar_status(self, ip_address):
        ip_address = self._normalize_ip(ip_address)
        record = self._normalize_record(self.repository.find_by_ip(ip_address))
        if not record:
            return None, self.DAILY_AVATAR_CHANGE_LIMIT
        return record.get("avatar_url"), self._remaining_avatar_changes(record)

    def save_avatar(self, ip_address, avatar_url):
        ip_address = self._normalize_ip(ip_address)
        record = self._normalize_record(self.repository.find_by_ip(ip_address))
        previous_url = record.get("avatar_url") if record else None
        today = date.today().isoformat()

        if previous_url == avatar_url:
            return avatar_url, previous_url

        if not record:
            self.repository.upsert_avatar(ip_address, avatar_url, 1, today)
            return avatar_url, None

        if record.get("avatar_changed_date") != today:
            self.repository.upsert_avatar(ip_address, avatar_url, 1, today)
            return avatar_url, previous_url

        change_count = int(record.get("avatar_change_count") or 0)
        if change_count >= self.DAILY_AVATAR_CHANGE_LIMIT:
            return None, previous_url

        change_count += 1
        self.repository.upsert_avatar(ip_address, avatar_url, change_count, today)
        return avatar_url, previous_url

    def _remaining_avatar_changes(self, record):
        if record.get("avatar_changed_date") != date.today().isoformat():
            return self.DAILY_AVATAR_CHANGE_LIMIT
        return max(0, self.DAILY_AVATAR_CHANGE_LIMIT - int(record.get("avatar_change_count") or 0))

    def _remaining_changes(self, record):
        if record.get("changed_date") != date.today().isoformat():
            return self.DAILY_NAME_CHANGE_LIMIT
        return max(0, self.DAILY_NAME_CHANGE_LIMIT - int(record.get("change_count") or 0))
