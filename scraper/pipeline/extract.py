from __future__ import annotations

import json

from bs4 import BeautifulSoup

from scraper.models import iso_date


def extract_article(html: str, source_config: dict) -> tuple[str | None, str | None, str]:
    soup = BeautifulSoup(html, "html.parser")
    for selector in source_config.get("remove_selectors", []):
        for node in soup.select(selector):
            node.decompose()

    title = _meta(soup, "property", "og:title") or _text(soup.title)
    published = (
        _meta(soup, "property", "article:published_time")
        or _meta(soup, "name", "date")
        or _json_ld_date(soup)
    )

    container = None
    for selector in source_config.get("body_selectors", ["article", "main"]):
        candidate = soup.select_one(selector)
        if candidate and len(candidate.get_text(" ", strip=True)) > 100:
            container = candidate
            break
    if container is None:
        container = soup.body or soup

    blocks = [
        node.get_text(" ", strip=True)
        for node in container.select("p, h2, h3, li")
        if node.get_text(" ", strip=True)
    ]
    body = "\n".join(blocks) if blocks else container.get_text("\n", strip=True)
    return title, iso_date(published), body


def _meta(soup: BeautifulSoup, key: str, value: str) -> str | None:
    node = soup.find("meta", attrs={key: value})
    return node.get("content") if node else None


def _text(node) -> str | None:
    return node.get_text(" ", strip=True) if node else None


def _json_ld_date(soup: BeautifulSoup) -> str | None:
    for node in soup.select("script[type='application/ld+json']"):
        try:
            data = json.loads(node.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("datePublished"):
                return str(item["datePublished"])
    return None

