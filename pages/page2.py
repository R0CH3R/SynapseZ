import storage
from models import Song
from youtube_service import (
    extract_youtube_video_id,
    fetch_youtube_video_metadata,
    get_youtube_api_key,
)

TITLE = "Add New Song (เพิ่มเพลงใหม่)"


def build(query=None):
    if query is None:
        query = {}

    yt_url = query.get("yt_url", "").strip()
    imported = None
    notice = ""

    if yt_url:
        video_id = extract_youtube_video_id(yt_url)
        if not video_id:
            notice = "ไม่สามารถระบุ YouTube Video ID จาก URL ได้ กรุณาตรวจสอบลิงก์อีกครั้ง"
        else:
            api_key = get_youtube_api_key()
            if not api_key:
                notice = "ไม่พบ YOUTUBE_API_KEY กรุณากำหนด API Key ในระบบหรือไฟล์ .env"
            else:
                data, err = fetch_youtube_video_metadata(video_id, api_key)
                if err:
                    notice = err
                else:
                    imported = data
                    notice = "✓ YouTube metadata imported"

    return {
        "yt_url": yt_url,
        "imported": imported,
        "notice": notice,
        "keep_genre": query.get("keep_genre", ""),
        "keep_rating": query.get("keep_rating", ""),
        "keep_plays": query.get("keep_plays", ""),
    }


def handle(form):
    title = form.get("title", "").strip()
    artist = form.get("artist", "").strip()
    genre = form.get("genre", "").strip()
    year = form.get("year", "").strip()
    rating = form.get("rating", "").strip()
    plays = form.get("plays", "").strip()

    if not title or not artist:
        return "กรุณากรอกชื่อเพลงและศิลปินให้เรียบร้อย"

    # สร้างออบเจกต์ Song พร้อมรองรับฟิลด์เพิ่มเติมจาก YouTube
    song = Song(
        title=title,
        artist=artist,
        genre=genre or "General",
        year=int(year) if year and year.isdigit() else 2026,
        rating=float(rating) if rating else 4.0,
        plays=int(plays) if plays and plays.isdigit() else 0,
        source=form.get("source", "").strip(),
        source_url=form.get("source_url", "").strip(),
        youtube_video_id=form.get("youtube_video_id", "").strip(),
        youtube_channel=form.get("youtube_channel", "").strip(),
        thumbnail_url=form.get("thumbnail_url", "").strip(),
        description=form.get("description", "").strip(),
    )

    songs = storage.load()
    songs.append(song.to_dict())
    storage.save(songs)

    return f"บันทึกเพลง '{title}' เข้าสู่ระบบเรียบร้อยแล้ว"
