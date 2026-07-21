from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RawArticle:
    url: str
    title: str | None
    published_date: str | None
    body_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunStats:
    articles_discovered: int = 0
    articles_fetched: int = 0
    articles_skipped: int = 0
    articles_failed: int = 0
    sentences_extracted: int = 0
    sentences_rejected: int = 0
    quota_skipped: int = 0
    duplicates_dropped: int = 0
    sentences_written: int = 0

    def add(self, other: "RunStats") -> None:
        for name in self.__dataclass_fields__:
            setattr(self, name, getattr(self, name) + getattr(other, name))


def iso_date(value: object) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return text[:10] if len(text) >= 10 else text
