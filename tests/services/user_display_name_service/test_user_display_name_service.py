import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.Services.UserDisplayNameService import UserDisplayNameService


class UserDisplayNameServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = UserDisplayNameService(repository=self.repo)

    def test_get_display_name_returns_default_when_no_record(self):
        self.repo.find_by_ip.return_value = None

        name, remaining = self.service.get_display_name("127.0.0.1, 10.0.0.1")

        self.assertIsNone(name)
        self.assertEqual(remaining, self.service.DAILY_NAME_CHANGE_LIMIT)
        self.repo.find_by_ip.assert_called_once_with("127.0.0.1")

    def test_get_display_name_returns_saved_name_and_remaining(self):
        self.repo.find_by_ip.return_value = {
            "display_name": "Joshua",
            "change_count": 2,
            "changed_date": date.today().isoformat(),
        }

        name, remaining = self.service.get_display_name("127.0.0.1")

        self.assertEqual(name, "Joshua")
        self.assertEqual(remaining, self.service.DAILY_NAME_CHANGE_LIMIT - 2)

    def test_get_display_name_resets_remaining_next_day(self):
        self.repo.find_by_ip.return_value = {
            "display_name": "Joshua",
            "change_count": 5,
            "changed_date": (date.today() - timedelta(days=1)).isoformat(),
        }

        name, remaining = self.service.get_display_name("127.0.0.1")

        self.assertEqual(name, "Joshua")
        self.assertEqual(remaining, self.service.DAILY_NAME_CHANGE_LIMIT)

    def test_save_display_name_creates_new_record(self):
        self.repo.find_by_ip.return_value = None

        name, remaining = self.service.save_display_name("127.0.0.1, 10.0.0.1", "  Joshua  ")

        self.assertEqual(name, "Joshua")
        self.assertEqual(remaining, self.service.DAILY_NAME_CHANGE_LIMIT - 1)
        self.repo.upsert_display_name.assert_called_once_with(
            "127.0.0.1", "Joshua", 1, date.today().isoformat()
        )

    def test_save_display_name_same_name_does_not_increment(self):
        self.repo.find_by_ip.return_value = {
            "display_name": "Joshua",
            "change_count": self.service.DAILY_NAME_CHANGE_LIMIT,
            "changed_date": date.today().isoformat(),
        }

        name, remaining = self.service.save_display_name("127.0.0.1", "Joshua")

        self.assertEqual(name, "Joshua")
        self.assertEqual(remaining, 0)
        self.repo.upsert_display_name.assert_not_called()

    def test_save_display_name_rejects_when_limit_reached(self):
        self.repo.find_by_ip.return_value = {
            "display_name": "Old",
            "change_count": self.service.DAILY_NAME_CHANGE_LIMIT,
            "changed_date": date.today().isoformat(),
        }

        name, remaining = self.service.save_display_name("127.0.0.1", "New Name")

        self.assertIsNone(name)
        self.assertEqual(remaining, 0)
        self.repo.upsert_display_name.assert_not_called()

    def test_save_display_name_increments_within_limit(self):
        self.repo.find_by_ip.return_value = {
            "display_name": "Old",
            "change_count": 2,
            "changed_date": date.today().isoformat(),
        }

        name, remaining = self.service.save_display_name("127.0.0.1", "New Name")

        self.assertEqual(name, "New Name")
        self.assertEqual(remaining, self.service.DAILY_NAME_CHANGE_LIMIT - 3)
        self.repo.upsert_display_name.assert_called_once_with(
            "127.0.0.1", "New Name", 3, date.today().isoformat()
        )

    def test_save_display_name_resets_count_next_day(self):
        self.repo.find_by_ip.return_value = {
            "display_name": "Old",
            "change_count": self.service.DAILY_NAME_CHANGE_LIMIT,
            "changed_date": (date.today() - timedelta(days=1)).isoformat(),
        }

        name, remaining = self.service.save_display_name("127.0.0.1", "New Name")

        self.assertEqual(name, "New Name")
        self.assertEqual(remaining, self.service.DAILY_NAME_CHANGE_LIMIT - 1)
        self.repo.upsert_display_name.assert_called_once_with(
            "127.0.0.1", "New Name", 1, date.today().isoformat()
        )

    def test_get_display_names_map_filters_blank_ips(self):
        self.repo.find_display_names_by_ips.return_value = {"127.0.0.1": "Joshua"}

        result = self.service.get_display_names_map(["127.0.0.1", "", "  "])

        self.assertEqual(result, {"127.0.0.1": "Joshua"})
        self.repo.find_display_names_by_ips.assert_called_once_with(["127.0.0.1"])

    def test_get_display_names_map_returns_empty_for_no_ips(self):
        result = self.service.get_display_names_map([])

        self.assertEqual(result, {})
        self.repo.find_display_names_by_ips.assert_not_called()

    def test_get_profile_returns_defaults_when_no_record(self):
        self.repo.find_by_ip.return_value = None

        name, avatar_url, remaining = self.service.get_profile("127.0.0.1, 10.0.0.1")

        self.assertIsNone(name)
        self.assertIsNone(avatar_url)
        self.assertEqual(remaining, self.service.DAILY_NAME_CHANGE_LIMIT)
        self.repo.find_by_ip.assert_called_once_with("127.0.0.1")

    def test_get_profile_returns_saved_name_avatar_and_remaining(self):
        self.repo.find_by_ip.return_value = {
            "display_name": "Joshua",
            "avatar_url": "/static/images/avatars/avatar_blue.svg",
            "change_count": 2,
            "changed_date": date.today().isoformat(),
        }

        name, avatar_url, remaining = self.service.get_profile("127.0.0.1")

        self.assertEqual(name, "Joshua")
        self.assertEqual(avatar_url, "/static/images/avatars/avatar_blue.svg")
        self.assertEqual(remaining, self.service.DAILY_NAME_CHANGE_LIMIT - 2)

    def test_get_profiles_map_delegates_to_repository(self):
        self.repo.find_profiles_by_ips.return_value = {
            "127.0.0.1": {"display_name": "Joshua", "avatar_url": "/a.webp"}
        }

        result = self.service.get_profiles_map(["127.0.0.1", "", "  "])

        self.assertEqual(result, {"127.0.0.1": {"display_name": "Joshua", "avatar_url": "/a.webp"}})
        self.repo.find_profiles_by_ips.assert_called_once_with(["127.0.0.1"])

    def test_get_profiles_map_returns_empty_for_no_ips(self):
        result = self.service.get_profiles_map([])

        self.assertEqual(result, {})
        self.repo.find_profiles_by_ips.assert_not_called()

    def test_save_avatar_upserts_and_returns_previous_url(self):
        self.repo.find_by_ip.return_value = {"avatar_url": "/old.webp"}

        new_url, previous_url = self.service.save_avatar("127.0.0.1, 10.0.0.1", "/new.webp")

        self.assertEqual(new_url, "/new.webp")
        self.assertEqual(previous_url, "/old.webp")
        self.repo.upsert_avatar.assert_called_once_with(
            "127.0.0.1", "/new.webp", 1, date.today().isoformat()
        )

    def test_save_avatar_returns_none_previous_when_no_record(self):
        self.repo.find_by_ip.return_value = None

        new_url, previous_url = self.service.save_avatar("127.0.0.1", "/new.webp")

        self.assertEqual(new_url, "/new.webp")
        self.assertIsNone(previous_url)
        self.repo.upsert_avatar.assert_called_once_with(
            "127.0.0.1", "/new.webp", 1, date.today().isoformat()
        )

    def test_save_avatar_same_avatar_does_not_increment(self):
        self.repo.find_by_ip.return_value = {
            "avatar_url": "/a.webp",
            "avatar_change_count": self.service.DAILY_AVATAR_CHANGE_LIMIT,
            "avatar_changed_date": date.today().isoformat(),
        }

        new_url, previous_url = self.service.save_avatar("127.0.0.1", "/a.webp")

        self.assertEqual(new_url, "/a.webp")
        self.assertEqual(previous_url, "/a.webp")
        self.repo.upsert_avatar.assert_not_called()

    def test_save_avatar_rejects_when_limit_reached(self):
        self.repo.find_by_ip.return_value = {
            "avatar_url": "/old.webp",
            "avatar_change_count": self.service.DAILY_AVATAR_CHANGE_LIMIT,
            "avatar_changed_date": date.today().isoformat(),
        }

        new_url, previous_url = self.service.save_avatar("127.0.0.1", "/new.webp")

        self.assertIsNone(new_url)
        self.assertEqual(previous_url, "/old.webp")
        self.repo.upsert_avatar.assert_not_called()

    def test_save_avatar_increments_within_limit(self):
        self.repo.find_by_ip.return_value = {
            "avatar_url": "/old.webp",
            "avatar_change_count": 2,
            "avatar_changed_date": date.today().isoformat(),
        }

        new_url, previous_url = self.service.save_avatar("127.0.0.1", "/new.webp")

        self.assertEqual(new_url, "/new.webp")
        self.assertEqual(previous_url, "/old.webp")
        self.repo.upsert_avatar.assert_called_once_with(
            "127.0.0.1", "/new.webp", 3, date.today().isoformat()
        )

    def test_save_avatar_resets_count_next_day(self):
        self.repo.find_by_ip.return_value = {
            "avatar_url": "/old.webp",
            "avatar_change_count": self.service.DAILY_AVATAR_CHANGE_LIMIT,
            "avatar_changed_date": (date.today() - timedelta(days=1)).isoformat(),
        }

        new_url, previous_url = self.service.save_avatar("127.0.0.1", "/new.webp")

        self.assertEqual(new_url, "/new.webp")
        self.assertEqual(previous_url, "/old.webp")
        self.repo.upsert_avatar.assert_called_once_with(
            "127.0.0.1", "/new.webp", 1, date.today().isoformat()
        )

    def test_get_avatar_status_returns_defaults_when_no_record(self):
        self.repo.find_by_ip.return_value = None

        avatar_url, remaining = self.service.get_avatar_status("127.0.0.1, 10.0.0.1")

        self.assertIsNone(avatar_url)
        self.assertEqual(remaining, self.service.DAILY_AVATAR_CHANGE_LIMIT)
        self.repo.find_by_ip.assert_called_once_with("127.0.0.1")

    def test_get_avatar_status_returns_url_and_remaining(self):
        self.repo.find_by_ip.return_value = {
            "avatar_url": "/a.webp",
            "avatar_change_count": 3,
            "avatar_changed_date": date.today().isoformat(),
        }

        avatar_url, remaining = self.service.get_avatar_status("127.0.0.1")

        self.assertEqual(avatar_url, "/a.webp")
        self.assertEqual(remaining, self.service.DAILY_AVATAR_CHANGE_LIMIT - 3)

    def test_get_avatar_status_resets_remaining_next_day(self):
        self.repo.find_by_ip.return_value = {
            "avatar_url": "/a.webp",
            "avatar_change_count": self.service.DAILY_AVATAR_CHANGE_LIMIT,
            "avatar_changed_date": (date.today() - timedelta(days=1)).isoformat(),
        }

        avatar_url, remaining = self.service.get_avatar_status("127.0.0.1")

        self.assertEqual(avatar_url, "/a.webp")
        self.assertEqual(remaining, self.service.DAILY_AVATAR_CHANGE_LIMIT)


if __name__ == "__main__":
    unittest.main()
