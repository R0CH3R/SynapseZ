import storage

TITLE = "Music Statistics & Overview (สถิติและภาพรวมเพลง)"


def calculate_genre_stats(songs):
    """คำนวณค่าเฉลี่ยและสถิติตามแนวเพลง (Genre)"""
    genre_data = {}
    for s in songs:
        genre = s.get("genre", "Other").strip() or "Other"
        rating = float(s.get("rating", 0))
        plays = int(s.get("plays", 0))

        if genre not in genre_data:
            genre_data[genre] = {"count": 0, "total_rating": 0.0, "total_plays": 0}

        genre_data[genre]["count"] += 1
        genre_data[genre]["total_rating"] += rating
        genre_data[genre]["total_plays"] += plays

    genre_bars = []
    for genre, data in genre_data.items():
        count = data["count"]
        avg_rating = round(data["total_rating"] / count, 2)
        avg_plays = int(data["total_plays"] / count)
        rating_percent = int((avg_rating / 5.0) * 100)

        genre_bars.append({
            "genre": genre,
            "count": count,
            "avg_rating": avg_rating,
            "avg_plays": avg_plays,
            "rating_percent": min(100, max(0, rating_percent)),
        })

    genre_bars.sort(key=lambda x: x["avg_rating"], reverse=True)
    return genre_bars


def calculate_song_bars(songs, avg_plays):
    """คำนวณกราฟแท่งเปรียบเทียบยอดฟังแต่ละเพลงกับค่าเฉลี่ย"""
    max_plays = max((int(s.get("plays", 0)) for s in songs), default=1)
    if max_plays <= 0:
        max_plays = 1

    bars = []
    for s in songs:
        plays = int(s.get("plays", 0))
        percent = int((plays * 100) / max_plays)
        is_above_avg = plays >= avg_plays
        bars.append({
            "title": s.get("title", ""),
            "artist": s.get("artist", ""),
            "plays": plays,
            "percent": min(100, max(0, percent)),
            "is_above_avg": is_above_avg,
        })

    bars.sort(key=lambda x: x["plays"], reverse=True)
    return bars


def build():
    songs = storage.load()

    total_songs = len(songs)
    total_plays = sum(int(s.get("plays", 0)) for s in songs)

    avg_rating = 0.0
    avg_plays = 0
    top_rated_song = None
    most_played_song = None

    if total_songs > 0:
        ratings = [float(s.get("rating", 0)) for s in songs]
        avg_rating = round(sum(ratings) / total_songs, 2)
        avg_plays = int(total_plays / total_songs)

        top_rated_song = max(songs, key=lambda s: float(s.get("rating", 0)))
        most_played_song = max(songs, key=lambda s: int(s.get("plays", 0)))

    genre_bars = calculate_genre_stats(songs)
    song_bars = calculate_song_bars(songs, avg_plays)

    avg_rating_percent = int((avg_rating / 5.0) * 100) if avg_rating > 0 else 0

    return {
        "songs": songs,
        "total_songs": total_songs,
        "total_plays": total_plays,
        "avg_rating": avg_rating,
        "avg_rating_percent": avg_rating_percent,
        "avg_plays": avg_plays,
        "top_rated_song": top_rated_song,
        "most_played_song": most_played_song,
        "genre_bars": genre_bars,
        "song_bars": song_bars,
    }