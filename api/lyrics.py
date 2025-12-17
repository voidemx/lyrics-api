import requests
import re
import base64
import random
from typing import Optional, Dict, Any
from cache import global_cache


class Lyrics:
    PAGE_SIZE = 8
    HEAD_CUT_LIMIT = 30
    DURATION_TOLERANCE = 8

    ACCEPTED_REGEX = re.compile(r"^\[(\d{1,2}):(\d{1,2})\.(\d{2,3})\].*")
    BANNED_REGEX = re.compile(r".+].+[:：].+")

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]

    def __init__(self):
        self.session = requests.Session()

    def fetch_json(self, url: str, params: Dict[str, Any]) -> Optional[Dict]:
        try:
            headers = {"User-Agent": random.choice(self.USER_AGENTS)}
            response = self.session.get(url, params=params, headers=headers, timeout=8)
            return response.json()
        except Exception:
            return None

    def normalize_title(self, title: str) -> str:
        t = str(title).strip()
        t = re.sub(r"\(.*\)|（.*）|「.*」|『.*』|<.*>|《.*》|〈.*〉|＜.*＞", "", t)
        return t.strip()

    def normalize_artist(self, artist: str) -> str:
        a = str(artist).strip()
        a = (
            a.replace(", ", "、")
            .replace(" & ", "、")
            .replace(".", "")
            .replace("和", "、")
        )
        a = re.sub(r"\(.*\)|（.*）", "", a)
        return a.strip()

    def normalize_content(self, base64_content: str) -> str:
        if not base64_content:
            return ""
        try:
            decoded = base64.b64decode(base64_content).decode("utf-8", errors="ignore")
            text = decoded.replace("&apos;", "'")
            lines = [
                line for line in text.splitlines() if self.ACCEPTED_REGEX.match(line)
            ]
            if not lines:
                return ""

            head_cut = 0
            for i in range(min(self.HEAD_CUT_LIMIT, len(lines) - 1), -1, -1):
                if self.BANNED_REGEX.match(lines[i]):
                    head_cut = i + 1
                    break

            filtered = lines[head_cut:]
            tail_cut = len(filtered)
            for i in range(max(0, len(filtered) - self.HEAD_CUT_LIMIT), len(filtered)):
                if self.BANNED_REGEX.match(filtered[i]):
                    tail_cut = i
                    break
            return "\n".join(filtered[:tail_cut])
        except Exception:
            return ""

    @global_cache.cached(ttl=3600)
    def search_songs(self, keyword: str) -> Optional[Dict]:
        return self.fetch_json(
            "https://mobileservice.kugou.com/api/v3/search/song",
            {
                "version": 9108,
                "plat": 0,
                "pagesize": self.PAGE_SIZE,
                "keyword": keyword,
            },
        )

    @global_cache.cached(ttl=3600)
    def search_lyrics(
        self, keyword: str = None, hash_str: str = None, duration: int = None
    ) -> Optional[Dict]:
        params = {"ver": 1, "man": "yes", "client": "pc"}
        if keyword:
            params["keyword"] = keyword
        if duration and duration != -1:
            params["duration"] = duration
        if hash_str:
            params["hash"] = hash_str
        return self.fetch_json("https://lyrics.kugou.com/search", params)

    @global_cache.cached(ttl=86400)
    def download_lyrics(self, id_val: str, access_key: str) -> Optional[Dict]:
        return self.fetch_json(
            "https://lyrics.kugou.com/download",
            {
                "fmt": "lrc",
                "charset": "utf8",
                "client": "pc",
                "ver": 1,
                "id": id_val,
                "accesskey": access_key,
            },
        )

    def get_lyrics_by_query(
        self, raw_title: str, raw_artist: str, duration: int
    ) -> Optional[str]:
        clean_title = self.normalize_title(raw_title)
        if raw_artist:
            clean_artist = self.normalize_artist(raw_artist)
            keyword = f"{clean_title} - {clean_artist}"
        else:
            keyword = clean_title

        songs = self.search_songs(keyword)
        candidate = None
        if songs and "data" in songs and "info" in songs["data"]:
            for song in songs["data"]["info"]:
                song_dur = song.get("duration", 0)
                if (
                    duration == -1
                    or abs(song_dur - duration) <= self.DURATION_TOLERANCE
                ):
                    res = self.search_lyrics(hash_str=song.get("hash"))
                    if res and res.get("candidates"):
                        candidate = res["candidates"][0]
                        break

        if not candidate:
            dur_ms = duration * 1000 if duration != -1 else None
            res = self.search_lyrics(keyword=keyword, duration=dur_ms)
            if res and res.get("candidates"):
                candidate = res["candidates"][0]

        if candidate:
            dl = self.download_lyrics(candidate["id"], candidate["accesskey"])
            return self.normalize_content(dl.get("content", "")) if dl else None
        return None


lyrics_engine = Lyrics()
