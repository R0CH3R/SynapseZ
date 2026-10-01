"""models.py — your one class lives here."""

class Song:
    def __init__(
        self,
        title,
        artist,
        genre,
        year,
        rating,
        plays,
        source="",
        source_url="",
        youtube_video_id="",
        youtube_channel="",
        thumbnail_url="",
        description=""
    ):
        self.title = title
        self.artist = artist
        self.genre = genre
        self.year = year
        self.rating = rating
        self.plays = plays
        self.source = source
        self.source_url = source_url
        self.youtube_video_id = youtube_video_id
        self.youtube_channel = youtube_channel
        self.thumbnail_url = thumbnail_url
        self.description = description

    def describe(self):
        return f"{self.title} by {self.artist} ({self.year})"

    def to_dict(self):
        data = {
            "title": self.title,
            "artist": self.artist,
            "genre": self.genre,
            "year": self.year,
            "rating": self.rating,
            "plays": self.plays,
        }
        if self.source:
            data["source"] = self.source
        if self.source_url:
            data["source_url"] = self.source_url
        if self.youtube_video_id:
            data["youtube_video_id"] = self.youtube_video_id
        if self.youtube_channel:
            data["youtube_channel"] = self.youtube_channel
        if self.thumbnail_url:
            data["thumbnail_url"] = self.thumbnail_url
        if self.description:
            data["description"] = self.description
        return data
