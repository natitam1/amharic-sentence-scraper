from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from scraper.models import RawArticle


class BaseAdapter(ABC):
    def __init__(self, source_id: str, config: dict, fetcher):
        self.source_id = source_id
        self.config = config
        self.fetcher = fetcher

    @abstractmethod
    def list_article_urls(self, since: date | None = None) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def fetch_article(self, url: str) -> RawArticle:
        raise NotImplementedError

