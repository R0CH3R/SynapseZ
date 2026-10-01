import random
import storage
from models import Song

TITLE = "Music Catalog (แคตตาล็อกเพลงทั้งหมด)"


def validate_song_data(form):
    """ตรวจสอบความถูกต้องของข้อมูลเพลงและข้อมูลตัวเลข"""
    title = form.get("title", "").strip()
    artist = form.get("artist", "").strip()
    genre = form.get("genre", "").strip()
    year_str = form.get("year", "").strip()
    rating_str = form.get("rating", "").strip()
    plays_str = form.get("plays", "").strip()

    if not title:
        return None, "กรุณาระบุชื่อเพลง"
    if not artist:
        return None, "กรุณาระบุชื่อศิลปิน"

    try:
        year = int(year_str) if year_str else 2026
        if year < 1900 or year > 2100:
            return None, "ปีที่ออกต้องอยู่ระหว่าง ค.ศ. 1900 - 2100"
    except ValueError:
        return None, "ปีที่ออกต้องเป็นตัวเลขจำนวนเต็ม"

    try:
        rating = float(rating_str) if rating_str else 0.0
        if rating < 0.0 or rating > 5.0:
            return None, "คะแนนเรตติ้งต้องอยู่ระหว่าง 0.0 ถึง 5.0"
    except ValueError:
        return None, "คะแนนเรตติ้งต้องเป็นตัวเลขทศนิยม"

    try:
        plays = int(plays_str) if plays_str else 0
        if plays < 0:
            return None, "จำนวนครั้งที่ฟังต้องไม่ติดลบ"
    except ValueError:
        return None, "จำนวนครั้งที่ฟังต้องเป็นตัวเลขจำนวนเต็มที่ไม่ติดลบ"

    return {
        "title": title,
        "artist": artist,
        "genre": genre or "General",
        "year": year,
        "rating": round(rating, 1),
        "plays": plays,
    }, ""


def build(query=None):
    if query is None:
        query = {}

    songs = storage.load()

    # ตรวจสอบการขอแก้ไขเพลง (?edit=index)
    edit_index = None
    editing_song = None
    edit_param = query.get("edit", "")
    if edit_param.isdigit():
        idx = int(edit_param)
        if 0 <= idx < len(songs):
            edit_index = idx
            editing_song = songs[idx]

    # นับจำนวนเพลงที่มียอดฟังสูง (> 2,000 ครั้ง)
    high_plays_count = 0
    for s in songs:
        if int(s.get("plays", 0)) > 2000:
            high_plays_count += 1

    featured_song = None
    if songs:
        chosen = random.choice(songs)
        featured_song = Song(
            title=chosen.get("title", ""),
            artist=chosen.get("artist", ""),
            genre=chosen.get("genre", ""),
            year=chosen.get("year", 2026),
            rating=chosen.get("rating", 0),
            plays=chosen.get("plays", 0),
        )

    return {
        "songs": songs,
        "featured_song": featured_song,
        "high_plays_count": high_plays_count,
        "edit_index": edit_index,
        "editing_song": editing_song,
    }


def handle(form):
    action = form.get("action")
    songs = storage.load()

    # 1. แก้ไขข้อมูลเพลง / ข้อมูลตัวเลข
    if action == "update":
        index = form.get("index", "")
        if not index.isdigit() or int(index) < 0 or int(index) >= len(songs):
            return "ไม่พบตำแหน่งเพลงที่ต้องการแก้ไข"

        idx = int(index)
        updated_data, err = validate_song_data(form)
        if err:
            return f"เกิดข้อผิดพลาด: {err}"

        songs[idx] = updated_data
        storage.save(songs)
        return f"แก้ไขข้อมูลเพลง '{updated_data['title']}' สำเร็จ (ยอดฟัง: {updated_data['plays']}, เรตติ้ง: {updated_data['rating']})"

    # 2. เพิ่มยอดฟังด่วน (+100 ครั้ง)
    elif action == "add_plays":
        index = form.get("index", "")
        amount_str = form.get("amount", "100")
        if index.isdigit() and int(index) < len(songs):
            idx = int(index)
            try:
                amt = int(amount_str)
            except ValueError:
                amt = 100
            current_plays = int(songs[idx].get("plays", 0))
            songs[idx]["plays"] = max(0, current_plays + amt)
            storage.save(songs)
            return f"เพิ่มยอดฟังเพลง '{songs[idx]['title']}' +{amt} ครั้ง (รวม {songs[idx]['plays']} ครั้ง)"
        return "ไม่พบเพลงที่ต้องการเพิ่มยอดฟัง"

    # 3. ลบเพลง
    elif action == "delete":
        title = form.get("title", "").strip()
        index = form.get("index", "")

        if index.isdigit():
            idx = int(index)
            if 0 <= idx < len(songs) and (not title or songs[idx].get("title") == title):
                deleted = songs.pop(idx)
                storage.save(songs)
                return f"ลบเพลง '{deleted.get('title')}' เรียบร้อยแล้ว"

        if title:
            for i, s in enumerate(songs):
                if s.get("title") == title:
                    deleted = songs.pop(i)
                    storage.save(songs)
                    return f"ลบเพลง '{deleted.get('title')}' เรียบร้อยแล้ว"

        return "ไม่พบเพลงที่ต้องการลบ"

    return "คำสั่งไม่ถูกต้อง"