import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.Services.MusicService import MusicService
from app.configurations import SortOrder

from tests.services._service_fixtures import music_doc


class MusicServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = MusicService(repository=self.repo)

    @patch("app.Services.MusicService.MutagenFile")
    def test_get_duration_formats_mm_ss(self, mock_mutagen):
        mock_mutagen.return_value = SimpleNamespace(info=SimpleNamespace(length=125.8))

        duration = self.service.get_duration("dummy.mp3")

        self.assertEqual(duration, "2:05")

    @patch("app.Services.MusicService.MutagenFile", side_effect=Exception("bad file"))
    def test_get_duration_returns_none_on_error(self, _mock_mutagen):
        self.assertIsNone(self.service.get_duration("dummy.mp3"))

    def test_get_music_by_id_returns_repository_value(self):
        self.repo.get_music_by_id.return_value = music_doc()

        result = self.service.get_music_by_id("m1")

        self.assertEqual(result["title"], "Song")
        self.repo.get_music_by_id.assert_called_once_with("m1")

    def test_get_music_by_url_returns_repository_value(self):
        self.repo.get_music_by_url.return_value = music_doc()

        result = self.service.get_music_by_url("/song.mp3")

        self.assertEqual(result["artist"], "Artist")
        self.repo.get_music_by_url.assert_called_once_with("/song.mp3")

    def test_get_paginated_music_list_maps_music_models(self):
        self.repo.get_paginated_music_list.return_value = ([music_doc()], 1)

        items, total = self.service.get_paginated_music_list(1, 10, SortOrder.DESC)

        self.assertEqual(total, 1)
        self.assertEqual(items[0].title, "Song")
        self.assertEqual(items[0].lyrics, "Lyrics")
        self.repo.get_paginated_music_list.assert_called_once_with(1, 10, SortOrder.DESC, "", "")

    def test_add_music_without_files_saves_model_and_normalizes_lyrics(self):
        self.repo.add_music.return_value = "m-new"

        result = self.service.add_music({"title": "Song", "artist": "Artist", "lyrics": None})

        self.assertEqual(result, "m-new")
        saved = self.repo.add_music.call_args[0][0].to_dict()
        self.assertTrue(saved["id"])
        self.assertEqual(saved["title"], "Song")
        self.assertEqual(saved["lyrics"], "")
        self.assertIsNone(saved["url"])
        self.assertIsNone(saved["image"])

    def test_update_music_returns_false_when_missing(self):
        self.repo.get_music_by_id.return_value = None

        result = self.service.update_music("m1", {"title": "New"})

        self.assertFalse(result)
        self.repo.update_music.assert_not_called()

    def test_update_music_without_new_files_keeps_existing_urls_and_updates_lyrics(self):
        self.repo.get_music_by_id.return_value = music_doc()
        self.repo.update_music.return_value = True

        result = self.service.update_music("m1", {"title": "Song 2", "artist": "Artist 2", "lyrics": "New lyrics"})

        self.assertTrue(result)
        args = self.repo.update_music.call_args[0]
        self.assertEqual(args[0], "m1")
        updated = args[1].to_dict()
        self.assertEqual(updated["title"], "Song 2")
        self.assertEqual(updated["artist"], "Artist 2")
        self.assertEqual(updated["lyrics"], "New lyrics")
        self.assertEqual(updated["url"], "/song.mp3")
        self.assertEqual(updated["image"], "/cover.jpg")
        self.assertEqual(updated["duration"], "1:23")

    @patch("app.Services.MusicService.cleanup_uploaded_files")
    def test_delete_music_cleans_up_and_deletes(self, mock_cleanup):
        self.repo.get_music_by_id.return_value = music_doc()
        self.repo.delete_music.return_value = True

        result = self.service.delete_music("m1")

        self.assertTrue(result)
        mock_cleanup.assert_called_once_with("/song.mp3", "/cover.jpg")
        self.repo.delete_music.assert_called_once_with("m1")


if __name__ == "__main__":
    unittest.main()
