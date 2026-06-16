class Music:
    def __init__(self, id, title, artist, url, image, duration, lyrics="", _id=None):
        self._id = _id
        self.id = id
        self.title = title
        self.artist = artist
        self.url = url
        self.image = image
        self.duration = duration
        self.lyrics = lyrics or ""

    def to_dict(self):
        data = {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "url": self.url,
            "image": self.image,
            "duration": self.duration,
            "lyrics": self.lyrics,
        }

        if self._id is not None:
            data["_id"] = str(self._id)

        return data

    @staticmethod
    def from_dict(data):
        return Music(
            _id=data.get("_id"),
            id=data.get("id"),
            title=data.get("title"),
            artist=data.get("artist"),
            url=data.get("url"),
            image=data.get("image"),
            duration=data.get("duration"),
            lyrics=data.get("lyrics", "")
        )
