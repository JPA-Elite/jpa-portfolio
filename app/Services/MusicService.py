import uuid
import subprocess
import json
import urllib.request
import re
import yt_dlp
from app.Repositories.Interfaces.IMusicRepository import IMusicRepository
from app.Models.Music import Music
from app.configurations import SortOrder
import tempfile, os
from app.constants.cloudinary import CloudinaryFolders, CloudinaryResourceType
from app.utils import cleanup_uploaded_files, convert_to_webp, upload_file_to_cloudinary
from mutagen import File as MutagenFile

class MusicService:
    def __init__(self, repository: IMusicRepository):
        self.repository = repository

    def get_duration(self, temp_path: str):
        try:
            duration_formatted = None
            audio = MutagenFile(temp_path)
            if audio and hasattr(audio, "info") and audio.info.length:
                total_seconds = round(audio.info.length, 2)
                minutes = int(total_seconds // 60)
                seconds = int(total_seconds % 60)

                duration_formatted = f"{minutes}:{seconds:02d}"

            return duration_formatted
        except Exception:
            return None

    def _extract_spotify_track_info(self, spotify_url: str):
        track_id_match = re.search(r"track/([a-zA-Z0-9]+)", spotify_url)
        if not track_id_match:
            return None, None

        track_id = track_id_match.group(1)
        oembed_url = f"https://open.spotify.com/oembed?url=spotify:track:{track_id}&format=json"

        try:
            req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
                title = data.get("title", "")
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    track_name = parts[0].strip()
                    artist = parts[1].strip()
                else:
                    track_name = title
                    artist = ""
                return track_name, artist
        except Exception:
            return None, None

    def _search_youtube_for_spotify_track(self, track_name: str, artist: str):
        queries = []
        if artist:
            queries = [
                f"{track_name} {artist} audio",
                f"{track_name} {artist}",
                f"{track_name} audio",
            ]
        else:
            queries = [
                f"{track_name} audio",
                f"{track_name} lyrics",
                f"{track_name} karaoke",
                track_name,
            ]

        ydl_opts = {'quiet': True, 'skip_download': True, 'no_warnings': True}

        for search_query in queries:
            try:
                ydl = yt_dlp.YoutubeDL(ydl_opts)
                results = ydl.extract_info(f'ytsearch1:{search_query}', download=False)
                if results and results.get('entries'):
                    entry = results['entries'][0]
                    return entry.get('url') or entry.get('webpage_url', '')
            except Exception:
                continue

        raise Exception(f"Could not find YouTube match for '{track_name}' by '{artist}'")

    def _download_audio_from_url(self, url: str):
        fd, out_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)

        original_url = url

        if "spotify.com/track/" in url:
            track_name, artist = self._extract_spotify_track_info(url)
            if not track_name:
                raise Exception(
                    "Cannot extract track info from Spotify URL. "
                    "Please provide a YouTube or direct audio URL instead."
                )
            url = self._search_youtube_for_spotify_track(track_name, artist)

        try:
            fd, temp_path = tempfile.mkstemp()
            os.close(fd)
            os.remove(temp_path)

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_path,
                'nocheckcertificate': True,
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            ydl.download([url])
            downloaded_files = [f for f in os.listdir(tempfile.gettempdir())
                            if f.startswith(os.path.basename(temp_path).rsplit(".", 1)[0])]
            if not downloaded_files:
                raise Exception("yt-dlp did not produce an output file")

            audio_file = os.path.join(tempfile.gettempdir(), downloaded_files[0])

            subprocess.run(
                ["ffmpeg", "-y", "-i", audio_file, "-vn", "-acodec", "libmp3lame", "-q:a", "0", out_path],
                capture_output=True, timeout=300
            )

            if os.path.exists(audio_file):
                os.remove(audio_file)

            if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
                raise Exception("ffmpeg conversion failed")
            return out_path
        except subprocess.TimeoutExpired:
            raise Exception("Download timed out")
        except Exception as e:
            if os.path.exists(out_path):
                os.remove(out_path)
            raise e

    # -------------------------- Music Service Methods -------------------------

    def get_music_by_id(self, music_id: str):
        return self.repository.get_music_by_id(music_id)

    def get_music_by_url(self, music_url: str):
        return self.repository.get_music_by_url(music_url)

    def get_paginated_music_list(self, page, per_page, order: SortOrder = SortOrder.DESC, search_query: str = "", category: str = ""):
        data, total_data = self.repository.get_paginated_music_list(page, per_page, order, search_query, category)
        system_info_list = [Music.from_dict(music) for music in data]
        return system_info_list, total_data

    def get_all_categories(self):
        """Get all unique categories from the database"""
        return self.repository.get_all_categories()

    def get_category_counts(self):
        """Get count of music grouped by category"""
        return self.repository.get_category_counts()

    def _resolve_music_file(self, data: dict):
        music_file = data.pop("music_file", None)
        music_url_input = data.pop("music_url_input", None)
        source_type = data.pop("music_source_type", "file")

        if source_type == "url" and music_url_input:
            return self._download_audio_from_url(music_url_input.strip())
        if music_file:
            fd, path = tempfile.mkstemp()
            os.close(fd)
            music_file.save(path)
            return path
        return None

    def add_music(self, data: dict):
        if "id" not in data or not data["id"]:
            data["id"] = str(uuid.uuid4())
        data["lyrics"] = data.get("lyrics") if isinstance(data.get("lyrics"), str) else ""
        data["category"] = data.get("category", "All")

        music_url, image_url = None, None
        duration = None
        temp_music_path = None

        try:
            temp_music_path = self._resolve_music_file(data)
            if temp_music_path:
                music_url = upload_file_to_cloudinary(
                    temp_music_path,
                    resource_type=CloudinaryResourceType.AUDIO,
                    folder=CloudinaryFolders.MUSIC
                )
                duration = self.get_duration(temp_music_path)
                os.remove(temp_music_path)
                temp_music_path = None

            image_file = data.pop("image_file", None)
            if image_file:
                fd, path = tempfile.mkstemp()
                os.close(fd)
                image_file.save(path)

                webp_path = convert_to_webp(path)

                image_url = upload_file_to_cloudinary(
                    webp_path,
                    resource_type=CloudinaryResourceType.IMAGE,
                    folder=CloudinaryFolders.MUSIC
                )
                os.remove(path)
                if webp_path != path:
                    os.remove(webp_path)

            data["url"] = music_url
            data["image"] = image_url
            data["duration"] = duration

            music = Music(**data)
            return self.repository.add_music(music)

        except Exception as e:
            cleanup_uploaded_files(music_url, image_url)
            raise e
        finally:
            if temp_music_path and os.path.exists(temp_music_path):
                os.remove(temp_music_path)

    def update_music(self, music_id: str, data: dict):
        existing_music = self.get_music_by_id(music_id)
        if not existing_music:
            return False

        update_data = {
            "title": data.get("title") or existing_music["title"],
            "artist": data.get("artist") or existing_music["artist"],
            "lyrics": data["lyrics"] if data.get("lyrics") is not None else existing_music.get("lyrics", ""),
            "category": data.get("category") or existing_music.get("category", "All"),
        }

        new_music_url, new_image_url = None, None
        duration = existing_music.get("duration") or None
        temp_music_path = None

        try:
            temp_music_path = self._resolve_music_file(data)
            if temp_music_path:
                if existing_music.get("url"):
                    cleanup_uploaded_files(existing_music["url"], None)

                new_music_url = upload_file_to_cloudinary(
                    temp_music_path,
                    resource_type=CloudinaryResourceType.AUDIO,
                    folder=CloudinaryFolders.MUSIC
                )

                duration = self.get_duration(temp_music_path)
                os.remove(temp_music_path)
                temp_music_path = None

                update_data["url"] = new_music_url
            else:
                update_data["url"] = existing_music.get("url")

            image_file = data.pop("image_file", None)
            if image_file:
                if existing_music.get("image"):
                    cleanup_uploaded_files(None, existing_music["image"])

                fd, path = tempfile.mkstemp()
                os.close(fd)
                image_file.save(path)

                webp_path = convert_to_webp(path)

                new_image_url = upload_file_to_cloudinary(
                    webp_path,
                    resource_type=CloudinaryResourceType.IMAGE,
                    folder=CloudinaryFolders.MUSIC
                )
                os.remove(path)
                if webp_path != path:
                    os.remove(webp_path)

                update_data["image"] = new_image_url
            else:
                update_data["image"] = existing_music.get("image")

            update_data["id"] = existing_music.get("id") or str(uuid.uuid4())
            update_data["duration"] = duration

            music = Music(**update_data)
            return self.repository.update_music(music_id, music)

        except Exception as e:
            cleanup_uploaded_files(new_music_url, new_image_url)
            raise e
        finally:
            if temp_music_path and os.path.exists(temp_music_path):
                os.remove(temp_music_path)

    def delete_music(self, music_id: str):
        existing_music = self.get_music_by_id(music_id)
        if not existing_music:
            return False

        cleanup_uploaded_files(existing_music.get("url"), existing_music.get("image"))
        return self.repository.delete_music(music_id)

    def get_total_music_count(self) -> int:
        return self.repository.get_total_music_count()
