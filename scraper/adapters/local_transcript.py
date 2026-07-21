from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from scraper.adapters.base_adapter import BaseAdapter
from scraper.models import RawArticle

TIMESTAMP_RE = re.compile(
    r"^(?:\d+\s*$|(?:\d{1,2}:)?\d{2}:\d{2}[.,]\d{3}\s*-->)",
    re.MULTILINE,
)
CUE_TAG_RE = re.compile(r"<[^>]+>|\{\\[^}]+\}")
SPEAKER_RE = re.compile(r"^\s*(?:[A-Z][\w .'-]{0,30}|[\u1200-\u137f]{1,30})\s*:\s*")


def caption_text(text: str, strip_speaker_labels: bool = True) -> str:
    lines = []
    previous = None
    for line in text.splitlines():
        value = html.unescape(line.strip())
        if not value or value == "WEBVTT" or TIMESTAMP_RE.match(value):
            continue
        value = CUE_TAG_RE.sub("", value)
        value = re.sub(r"(?:>>+|\[[^\]]{1,60}\])", " ", value)
        value = re.sub(r"\s+", " ", value).strip()
        if strip_speaker_labels:
            value = SPEAKER_RE.sub("", value)
        if value and value != previous:
            lines.append(value)
            previous = value
    return " ".join(lines)


class LocalTranscriptAdapter(BaseAdapter):
    """Read permitted local transcripts without changing the shared pipeline."""

    def list_article_urls(self, since=None) -> list[str]:
        del since
        paths: list[Path] = []
        for pattern in self.config.get("paths", []):
            candidate = Path(pattern)
            if candidate.is_file():
                paths.append(candidate)
                continue
            base = Path(self.config.get("base_path", "."))
            paths.extend(base.glob(pattern))
        allowed = {".txt", ".jsonl", ".srt", ".vtt"}
        return [str(path.resolve()) for path in sorted(set(paths)) if path.suffix.lower() in allowed]

    def fetch_article(self, url: str) -> RawArticle:
        path = Path(url)
        text = path.read_text(encoding="utf-8-sig")
        if path.suffix.lower() == ".jsonl":
            text = self._jsonl_text(text)
        elif path.suffix.lower() in {".srt", ".vtt"}:
            text = caption_text(text, self.config.get("strip_speaker_labels", True))
        published = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).date().isoformat()
        return RawArticle(
            url=path.as_uri(),
            title=path.stem,
            published_date=published,
            body_text=text,
            metadata={"document_id": path.stem},
        )

    def _jsonl_text(self, text: str) -> str:
        field_name = self.config.get("text_field", "text")
        values = []
        for number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {number}: {exc}") from exc
            value = record.get(field_name)
            if value:
                values.append(str(value))
        return "\n".join(values)
