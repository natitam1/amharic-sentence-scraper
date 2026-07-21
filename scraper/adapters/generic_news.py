from __future__ import annotations

from datetime import date, datetime, timezone
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import feedparser
from bs4 import BeautifulSoup

from scraper.adapters.base_adapter import BaseAdapter
from scraper.models import RawArticle
from scraper.pipeline.extract import extract_article


class GenericNewsAdapter(BaseAdapter):
    def list_article_urls(self, since: date | None = None) -> list[str]:
        discovery = self.config["discovery"]
        kind = discovery["type"]
        urls: list[str] = []
        for discovery_url in discovery.get("urls", []):
            response = self.fetcher.get(discovery_url, self.config.get("delay_seconds"))
            if kind == "rss":
                urls.extend(self._from_feed(response.content, since))
            elif kind == "sitemap":
                urls.extend(self._from_sitemap(response.content))
            elif kind == "category":
                urls.extend(self._from_category(response.text, discovery_url))
            else:
                raise ValueError(f"Unsupported discovery type: {kind}")
        return list(dict.fromkeys(url for url in urls if self._is_article_url(url)))

    def fetch_article(self, url: str) -> RawArticle:
        response = self.fetcher.get(url, self.config.get("delay_seconds"))
        title, published, body = extract_article(response.text, self.config)
        return RawArticle(url=url, title=title, published_date=published, body_text=body)

    def _from_feed(self, content: bytes, since: date | None) -> list[str]:
        feed = feedparser.parse(content)
        result = []
        for entry in feed.entries:
            link = entry.get("link")
            if not link:
                continue
            if since:
                struct = entry.get("published_parsed") or entry.get("updated_parsed")
                if struct and date(*struct[:3]) < since:
                    continue
            result.append(link)
        return result

    def _from_sitemap(self, content: bytes) -> list[str]:
        root = ElementTree.fromstring(content)
        locations = [
            node.text.strip()
            for node in root.iter()
            if node.tag.endswith("loc") and node.text
        ]
        # Sitemap indexes are intentionally not recursively expanded without a
        # configured bound; add child sitemap URLs to config as needed.
        return [url for url in locations if not url.lower().endswith((".xml", ".xml.gz"))]

    @staticmethod
    def _from_category(html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        return [
            urljoin(page_url, node["href"])
            for node in soup.select("a[href]")
            if node.get("href")
        ]

    def _is_article_url(self, url: str) -> bool:
        base_host = urlparse(self.config["base_url"]).netloc.removeprefix("www.")
        host = urlparse(url).netloc.removeprefix("www.")
        if host != base_host:
            return False
        patterns = self.config.get("article_url_patterns", [])
        return not patterns or any(pattern in url for pattern in patterns)

