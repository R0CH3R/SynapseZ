"""youtube_service.py — Helper functions for extracting YouTube video ID and fetching metadata via YouTube Data API v3."""

import json
import os
import re
import urllib.error
import urllib.request
from urllib.parse import parse_qs, urlencode, urlparse


def load_env():
    """Load key-value pairs from .env file into os.environ without third-party dependencies."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, ".env")
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


def get_youtube_api_key():
    """Get the YouTube Data API v3 key from environment variables or .env file."""
    load_env()
    return os.environ.get("YOUTUBE_API_KEY", "").strip()


def extract_youtube_video_id(url):
    """
    Extract 11-character YouTube video ID from various URL formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - URLs containing additional query parameters (&t=..., &list=..., etc.)
    - Direct 11-char ID
    """
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    if not url:
        return None

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    # Short links: youtu.be/VIDEO_ID
    if "youtu.be" in hostname:
        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if parts and re.fullmatch(r"[A-Za-z0-9_-]{11}", parts[0]):
            return parts[0]

    # Standard YouTube links: youtube.com/...
    if "youtube.com" in hostname or "youtube-nocookie.com" in hostname:
        # /watch?v=VIDEO_ID
        if parsed.path.startswith("/watch"):
            qs = parse_qs(parsed.query)
            v = qs.get("v")
            if v and re.fullmatch(r"[A-Za-z0-9_-]{11}", v[0]):
                return v[0]

        # /shorts/VIDEO_ID or /embed/VIDEO_ID or /v/VIDEO_ID
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2 and parts[0] in ("shorts", "embed", "v"):
            if re.fullmatch(r"[A-Za-z0-9_-]{11}", parts[1]):
                return parts[1]

    # Regex search for v=... or /shorts/... or youtu.be/...
    match = re.search(r"(?:v=|\/shorts\/|\/embed\/|youtu\.be\/|\/v\/)([A-Za-z0-9_-]{11})", url)
    if match:
        return match.group(1)

    # Raw 11-char ID
    if "/" not in url and "." not in url and re.fullmatch(r"[A-Za-z0-9_-]{11}", url):
        return url

    return None


def fetch_youtube_video_metadata(video_id, api_key):
    """
    Fetch video metadata from YouTube Data API v3.
    Endpoint: https://www.googleapis.com/youtube/v3/videos?part=snippet&id=VIDEO_ID&key=API_KEY

    Returns:
        (metadata_dict, error_message)
    """
    if not api_key:
        return None, "กรุณากำหนด YOUTUBE_API_KEY ในไฟล์ .env หรือ Environment Variable"

    if not video_id:
        return None, "ไม่พบรหัสวิดีโอ YouTube (Video ID)"

    params = {
        "part": "snippet",
        "id": video_id,
        "key": api_key,
    }
    endpoint = "https://www.googleapis.com/youtube/v3/videos?" + urlencode(params)

    req = urllib.request.Request(
        endpoint,
        headers={"User-Agent": "SynapseZ-MusicApp/1.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                return None, f"เกิดข้อผิดพลาดจาก YouTube API (HTTP {response.status})"
            raw = response.read().decode("utf-8")
            data = json.loads(raw)
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP {e.code}"
        try:
            err_body = e.read().decode("utf-8", errors="replace")
            err_json = json.loads(err_body)
            reasons = [item.get("reason", "") for item in err_json.get("error", {}).get("errors", [])]
            msg = err_json.get("error", {}).get("message", "")
            if "quotaExceeded" in reasons or "quota" in msg.lower():
                return None, "โควตา YouTube Data API v3 เกินกำหนด (Quota exceeded)"
            if "keyInvalid" in reasons or "badRequest" in reasons or "API key not valid" in msg:
                return None, "API Key ของ YouTube ไม่ถูกต้อง (Invalid API Key)"
            if msg:
                error_msg = msg
        except Exception:
            pass
        return None, f"YouTube API ขัดข้อง: {error_msg}"
    except urllib.error.URLError:
        return None, "ไม่สามารถเชื่อมต่ออินเทอร์เน็ตเพื่อดึงข้อมูลจาก YouTube ได้"
    except Exception as e:
        return None, f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}"

    items = data.get("items", [])
    if not items:
        return None, "ไม่พบวิดีโอ YouTube นี้ (วิดีโออาจถูกลบ ตั้งค่าเป็นส่วนตัว หรือระบุ ID ไม่ถูกต้อง)"

    snippet = items[0].get("snippet", {})
    title = snippet.get("title", "").strip()
    channel_title = snippet.get("channelTitle", "").strip()
    published_at = snippet.get("publishedAt", "")
    description = snippet.get("description", "").strip()

    # Extract year from publishedAt (e.g., 2024-03-12T...)
    year = 2026
    if published_at and len(published_at) >= 4 and published_at[:4].isdigit():
        year = int(published_at[:4])

    # Extract best available thumbnail URL
    thumbnails = snippet.get("thumbnails", {})
    thumbnail_url = ""
    for quality in ["high", "medium", "standard", "default", "maxres"]:
        if quality in thumbnails and "url" in thumbnails[quality]:
            thumbnail_url = thumbnails[quality]["url"]
            if quality in ("high", "medium"):
                break

    return {
        "title": title,
        "artist": channel_title,
        "year": year,
        "source": "youtube",
        "source_url": f"https://www.youtube.com/watch?v={video_id}",
        "youtube_video_id": video_id,
        "youtube_channel": channel_title,
        "thumbnail_url": thumbnail_url,
        "description": description[:300] if description else "",
    }, ""
