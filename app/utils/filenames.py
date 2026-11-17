import re
import unicodedata
from urllib.parse import quote


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|;,]', '', name)


def ascii_fallback(name: str):
    normalized = unicodedata.normalize("NFKD", name)
    ascii_bytes = normalized.encode("ascii", "ignore")
    s = ascii_bytes.decode("ascii", "ignore")
    s = re.sub(r'[\\/*?:"<>|]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s or "download"


def safe_filename_parts(raw_title: str, raw_artist: str, ext: str = "mp3"):
    combined = f"{raw_title} - {raw_artist}".strip()
    fallback = ascii_fallback(combined)
    utf8_quoted = quote(combined, safe='')
    return fallback, utf8_quoted
