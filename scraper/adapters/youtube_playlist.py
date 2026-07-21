from __future__ import annotations

from datetime import date
import time
from typing import Any

from scraper.adapters.base_adapter import BaseAdapter
from scraper.adapters.local_transcript import caption_text
from scraper.models import RawArticle


class YouTubePlaylistAdapter(BaseAdapter):
    """Enumerate a YouTube playlist and retrieve subtitle text without media."""

    def _options(self, **overrides: Any) -> dict[str, Any]:
        options: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "ignoreerrors": True,
        }
        player_clients = self.config.get("player_clients")
        if player_clients:
            options["extractor_args"] = {"youtube": {"player_client": player_clients}}
        cookie_file = self.config.get("cookie_file")
        if cookie_file:
            options["cookiefile"] = cookie_file
        options.update(overrides)
        return options

    def list_article_urls(self, since: date | None = None) -> list[str]:
        del since
        from yt_dlp import YoutubeDL

        urls: list[str] = []
        options = self._options(extract_flat="in_playlist", noplaylist=False)
        with YoutubeDL(options) as ydl:
            collection_urls = self.config.get("collection_urls", self.config.get("playlist_urls", []))
            for collection_url in collection_urls:
                info = ydl.extract_info(collection_url, download=False)
                for entry in (info or {}).get("entries") or []:
                    if not entry:
                        continue
                    if not entry.get("title") and entry.get("duration") is None:
                        continue
                    video_id = entry.get("id")
                    if video_id:
                        urls.append(f"https://www.youtube.com/watch?v={video_id}")
        return list(dict.fromkeys(urls))

    def fetch_article(self, url: str) -> RawArticle:
        from yt_dlp import YoutubeDL

        time.sleep(float(self.config.get("request_delay_seconds", 3.0)))
        with YoutubeDL(self._options()) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError(f"YouTube video is unavailable: {url}")
            language, track, automatic = self._select_subtitle(info)
            if not track:
                raise ValueError(f"No configured Amharic captions found for {url}")
            raw = self._download_caption(ydl, track["url"], url)

        text = caption_text(raw, self.config.get("strip_speaker_labels", True))
        if not text.strip():
            raise ValueError(f"Caption track was empty for {url}")
        upload_date = info.get("upload_date")
        published = (
            f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
            if upload_date and len(upload_date) == 8
            else None
        )
        video_id = info.get("id")
        return RawArticle(
            url=f"https://www.youtube.com/watch?v={video_id}" if video_id else url,
            title=info.get("title"),
            published_date=published,
            body_text=text,
            metadata={
                "video_id": video_id,
                "channel": info.get("channel") or info.get("uploader"),
                "duration_seconds": info.get("duration"),
                "transcript_language": language,
                "automatic_captions": automatic,
            },
        )

    def _download_caption(self, ydl, track_url: str, video_url: str) -> str:
        retries = int(self.config.get("subtitle_retries", 3))
        backoff = float(self.config.get("subtitle_backoff_seconds", 20))
        last_error = None
        for attempt in range(retries):
            try:
                response = ydl.urlopen(track_url)
                return response.read().decode("utf-8", errors="replace")
            except Exception as exc:
                last_error = exc
                if attempt + 1 < retries:
                    time.sleep(backoff * (2**attempt))
        raise ValueError(f"Could not fetch captions for {video_url}: {last_error}")

    def _select_subtitle(self, info: dict) -> tuple[str | None, dict | None, bool]:
        requested = self.config.get("subtitle_languages", ["am", "am-ET"])
        sources = [
            (info.get("subtitles") or {}, False),
            (info.get("automatic_captions") or {}, True),
        ]
        for tracks, automatic in sources:
            for wanted in requested:
                matching = [key for key in tracks if key == wanted or key.startswith(f"{wanted}-")]
                for language in matching:
                    formats = tracks.get(language) or []
                    track = next((item for item in formats if item.get("ext") == "vtt"), None)
                    if track and track.get("url"):
                        return language, track, automatic
        return None, None, False

